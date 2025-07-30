import numpy as np
from numpy import ndarray
import tqdm
import astra
from astra.pythonutils import geom_size
import math
from copy import deepcopy
import logging

# from functools import wraps
from typing import Literal, Any, Tuple, Optional, Union
from types import ModuleType
from numpy.typing import ArrayLike
from collections.abc import Callable, Sequence
from numbers import Number

logger = logging.getLogger(__name__)
default_pbar = tqdm.tqdm
projection_algorithms = ("FP3D_CUDA", "FP_CUDA")
reconstruction_algorithms = (
    "BP_CUDA",
    "FBP_CUDA",
    "SIRT_CUDA",
    "SART_CUDA",
    "CGLS_CUDA",
    "CGLS_CUDA",
    "FDK_CUDA",
    "BP3D_CUDA",
    "SIRT3D_CUDA",
    "CGLS3D_CUDA",
)
Geometry = dict
ProjectionGeometry = dict
VolumeGeometry = dict
AlgorithmConfiguration = dict


def idop(x: Any) -> Any:  # identity operator
    return x


class AstraAlgorithm:
    id: int

    # @wraps(astra.algorithm.create)
    def __init__(self, alg_cfg: AlgorithmConfiguration) -> None:
        self.id = astra.algorithm.create(alg_cfg)

    # @wraps(astra.algorithm.run)
    def run(self, iterations: int = 1) -> None:
        astra.algorithm.run(self.id, iterations)

    def __del__(self) -> None:
        astra.algorithm.delete(self.id)


class AstraData:
    datatype: Literal["-sino", "-vol"]
    shape: tuple
    ndim: Literal[1, 2]
    module: ModuleType
    id: Optional[int]

    def __init__(
        self,
        datatype: Literal["-sino", "-vol"],
        geometry: Geometry,
        data: Optional[ArrayLike] = None,
        link: bool = False,
    ) -> None:
        self.datatype = datatype
        self.shape = geom_size(geometry)
        self.ndim = len(self.shape)
        self._geometry = geometry
        match self.ndim:
            case 2:
                self.module = astra.data2d
            case 3:
                self.module = astra.data3d
            case _:
                raise ValueError(f"{self.ndim = }")
        self.id = None
        if data is not None:
            self.load(data, link)

    def init_array(self, link=False):
        if link:
            self.array = np.empty(self.shape, np.float32)
            self.load(self.array, link=True)
        else:
            self.id = self.module.create(self.datatype, self.geometry)

    @property
    def geometry(self) -> Geometry:
        if self.id is not None:
            return self.module.get_geometry(self.id)
        else:
            return self._geometry

    @geometry.setter
    def geometry(self, geometry: Geometry) -> None:
        if self.id is not None:
            self.module.change_geometry(self.id, geometry)
        else:
            self._geometry = geometry

    def load(self, data: ArrayLike, link=False) -> None:
        if link:
            old_id = self.id
            if not (data.flags["C_CONTIGUOUS"] and data.flags["ALIGNED"]):
                raise ValueError(
                    "Numpy array should be C_CONTIGUOUS and ALIGNED to allow linking.\n"
                    "Consider making it linkable with `array = self.linkable_proj_array(array)`"
                )
            self.id = self.module.link(self.datatype, self.geometry, data)
            if old_id is not None:
                self.module.delete(old_id)
        else:
            if self.id is None:
                self.id = self.module.create(self.datatype, self.geometry, data)
            else:
                self.module.store(self.id, data)

    def get(self) -> ndarray:
        return self.module.get(self.id)

    def __del__(self) -> None:
        if self.id is not None:
            self.module.delete(self.id)


class AstraTomo:
    ndim: int
    sino_pad: int
    det_shape: tuple
    alg_cfg: dict

    def __init__(
        self,
        p_geometry: ProjectionGeometry,
        v_geometry: VolumeGeometry,
        alg_cfg: AlgorithmConfiguration,
        sino_pad: int = 0,
        proj: ArrayLike = None,
    ) -> None:
        full_shape = geom_size(p_geometry)
        self.ndim = len(full_shape)
        self.sino_pad = sino_pad
        self.det_shape = (
            full_shape[0],
            full_shape[-1] - 2 * sino_pad,
        )
        self._projections = AstraData("-sino", p_geometry, data=proj)
        self._volume = AstraData("-vol", v_geometry)
        self.alg_cfg = alg_cfg

    @property
    def p_geometry(self) -> ProjectionGeometry:
        return self._projections.geometry

    @p_geometry.setter
    def p_geometry(self, new_geom: ProjectionGeometry) -> None:
        """Replace the projection geometry."""
        self._projections.geometry = new_geom

    @property
    def angles(self) -> ndarray:
        return get_angles(self.p_geometry)

    @property
    def projections(self) -> ndarray:
        proj = self.proj_transform(self._projections.get())
        if self.sino_pad != 0:
            proj = proj[..., self.sino_pad : -self.sino_pad]
        return proj

    @projections.setter
    def projections(self, value: Any) -> None:
        raise ValueError("please use set_projections instead of setting this value directly")

    def set_projections(self, proj: ArrayLike, link: bool = False) -> None:
        # proj (out)       : (nangles, height, width) or (nangles, width)  - irp default
        # self._projections: (height, nangles, width) or (nangles, width)  - astra convention
        # untangling is done with self.proj_transform

        if self.sino_pad > 0:
            padding = ((0, 0),) * (self.ndim - 1) + ((self.sino_pad, self.sino_pad),)
            proj = np.pad(proj, padding, mode="edge")
        proj = self.proj_transform(proj)
        self._projections.load(proj, link)

    @property
    def volume(self) -> ndarray:
        # 2d tomo overwrites this to flip dim 0
        return self._volume.get()

    @volume.setter
    def volume(self, value: Any) -> None:
        raise ValueError("please use set_volume instead of setting this value directly")

    def set_volume(self, data: ArrayLike, link: bool = False) -> None:
        self._volume.load(data, link)

    def project(
        self, vol: Optional[ArrayLike] = None, link: bool = False, get_data: bool = True
    ) -> Union[ndarray, None]:
        if vol is not None:
            self.set_volume(vol, link)
        elif self._volume.id is None:
            raise ValueError("no volume data found")

        if self._projections.id is None:
            self._projections.init_array()

        alg_cfg = algorithm_config(self.forward_algorithm)
        self.create_algorithm(alg_cfg).run(1)

        if get_data:
            return self.projections

    def create_algorithm(self, alg_cfg: AlgorithmConfiguration) -> AstraAlgorithm:
        if alg_cfg["type"] in projection_algorithms:
            alg_cfg["VolumeDataId"] = self._volume.id
        elif alg_cfg["type"] in reconstruction_algorithms:
            alg_cfg["ReconstructionDataId"] = self._volume.id
        else:
            raise ValueError(f"no defaults for algorithm {alg_cfg['type']} found.")
        alg_cfg["ProjectionDataId"] = self._projections.id

        return AstraAlgorithm(alg_cfg)

    def reconstruct(
        self,
        proj: Optional[ArrayLike] = None,
        iterations: int = 1,
        get_data: bool = True,
        link: bool = False,
    ) -> Union[ndarray, None]:
        """Reconstruct projections."""
        if proj is not None:
            self.set_projections(proj, link=link)
        elif self._projections.id is None:
            raise ValueError("no projection data found")

        if self._volume.id is None:
            self._volume.init_array()

        self.create_algorithm(self.alg_cfg).run(iterations)

        if get_data:
            return self.volume

    def apply_shift(
        self, shift: ArrayLike, reference_geom: Optional[ProjectionGeometry] = None, move="detector"
    ) -> None:
        """Correct geometry for detector shift."""
        if reference_geom is None:
            reference_geom = self.p_geometry
        else:
            reference_geom = deepcopy(reference_geom)
        self.p_geometry = shift_geometry(reference_geom, shift, move=move)

    def apply_constraint(self, constraint: Callable[[ArrayLike], ArrayLike]) -> None:
        # would be nice, if we could multiply directly on GPU
        self.set_volume(constraint(self.volume))

    def proj_transform(self, proj: ndarray, inverse: bool = False) -> ndarray:
        return proj

    def linkable_proj_array(self, proj: ndarray) -> ndarray:
        return self.proj_transform(
            np.ascontiguousarray(self.proj_transform(proj)),
            inverse=True,
        )


class AstraTomo2D(AstraTomo):
    forward_algorithm = "FP_CUDA"

    def set_volume(self, data: ArrayLike, link: bool = False) -> None:
        self._volume.load(np.flip(data, 0), link)

    @property
    def volume(self) -> ndarray:
        # flip dim 0
        return np.flip(self._volume.get(), 0)

    def project_stack(
        self,
        vol: ArrayLike,
        link: bool = False,
        pbar: Optional[Callable[[ndarray], ndarray]] = None,
    ) -> ndarray:
        """
        Project each volume slice
        parameters
            vol: (height, width, width)
        returns
            projections: (nangles, height, width)
        """
        if pbar is None:
            pbar = default_pbar

        if self._projections.id is None:
            self._projections.init_array()
        self.set_volume(vol[0], link)  # algorithm init requires volume data object

        alg_cfg = algorithm_config(self.forward_algorithm)
        alg = self.create_algorithm(alg_cfg)

        nangles = self._projections.shape[-2]
        width = self._projections.shape[-1]
        projections = np.empty((nangles, len(vol), width), np.float32)

        pbar = pbar or idop  # use idop when set to None
        for i, vol_slice in enumerate(pbar(vol)):
            self.set_volume(vol_slice, link)
            alg.run(1)
            projections[:, i] = self.projections

        return projections

    def reconstruct_stack(
        self,
        proj: ArrayLike,
        iterations: int = 1,
        link: bool = False,
        pbar: Optional[Callable[[ndarray], ndarray]] = None,
    ) -> ndarray:
        """
        Reconstruct a stack of volume slices from a stack of projection slices (sinograms).
        parameters
            proj: (nangles, height, width)
        returns
            vol_reco: (height, width, width)
        """
        if pbar is None:
            pbar = default_pbar
        alg = self.create_algorithm(self.alg_cfg)

        height = proj.shape[1]
        vol_reco = np.empty((height, *self._volume.shape), np.float32)

        pbar = pbar or idop  # use idop when set to None
        for i in pbar(range(height)):
            self.set_projections(proj[:, i], link)
            alg.run(iterations)
            vol_reco[i] = self._volume.get()

        return vol_reco


class AstraTomo3D(AstraTomo):
    forward_algorithm = "FP3D_CUDA"

    def proj_transform(self, proj: ndarray, inverse=False) -> ndarray:
        return proj.swapaxes(0, 1)

    def roll_rotaxis(
        self,
        angle_deg: Union[float, ArrayLike],
        reference_geom: Optional[ProjectionGeometry] = None,
    ) -> None:
        """rotate the rotation axis in beam direction"""
        if reference_geom is None:
            reference_geom = self.p_geometry
        else:
            reference_geom = deepcopy(reference_geom)
        self.p_geometry = geo_roll_rotaxis(reference_geom, angle_deg)

    def pitch_rotaxis(
        self,
        angle_deg: Union[float, ArrayLike],
        reference_geom: Optional[ProjectionGeometry] = None,
    ) -> None:
        """pitch (or nick) rotation of the rotation axis"""
        if reference_geom is None:
            reference_geom = self.p_geometry
        else:
            reference_geom = deepcopy(reference_geom)
        self.p_geometry = geo_pitch_rotaxis(reference_geom, angle_deg)


def _transform_geo_pars(
    z01: ArrayLike, z02: ArrayLike, px: ArrayLike
) -> Tuple[ArrayLike, ArrayLike, ArrayLike]:
    """
    z01: source-sample distance
    z02: source-detector distance
    dx: pixel pitch

    returns:
        m: magnification, which is also px / px_eff
        z01_eff: source-object distance / px_eff
        z12_eff: object-detector distance / px_eff
    """
    m = z02 / z01
    px_eff = px / m
    z01_eff = z01 / px_eff
    z12_eff = (z02 - z01) / px_eff

    return m, z01_eff, z12_eff


def algorithm_config(alg: Union[str, dict]) -> dict:
    """
    Create and add defaults to astra algorithm configuration.

    Example
    --------
    >>> import astra
    >>> from hotopy import tomo
    >>> alg_cfg = tomo.algorithm_config("FBP_CUDA")
    >>> alg_cfg["FilterType"] = "hamming"

    """
    if isinstance(alg, str):
        alg = {"type": alg}

    if alg["type"].upper().startswith("FBP"):
        alg.setdefault("FilterType", "Ram-Lak")
    return alg


def setup(
    det_shape: Union[int, Sequence, ArrayLike],
    angles: ArrayLike,
    cone: Optional[Tuple[float, float, float]] = None,  # (z01, z02, px)
    sino_pad: Union[int, Literal["corner"]] = 0,
    voxel_size: float = 1,
    nslices: Optional[int] = None,
    algorithm: Union[str, dict, None] = None,
) -> AstraTomo:
    """Create astra tomography wrapper from few parameters.

    Parameters
    ----------
    det_shape: int | Sequence | ArrayLike
        Number of detector pixels (rows (if present), columns). A tuple of length 2 initializes
        a three dimensional geometry, a single number or tuple of length one a two dimensional one.
    angles: ArrayLike
        Tomographic angles in radians. Positive angles mean the object rotates around an axis
        pointing up (positive z) in the fixed lab frame.
    cone: None | tuple: (z01, z02, px) (optional)
        Set to None for parallel geometries. For cone- or fan geometries specify:
        (source-object distance, source-detector distance, detector pixel size). Default: None
    sino_pad: int (optional)
        Number of pixels to add to the sides of the sinogram. This can mitigate artifacts outside
        of the reconstruction cylinder. Default: 0
    voxel_size: float (optional)
        The voxel size in the volume divided by the demagnified detector pixel size allows an upsampled
        (< 1) and downsampled (> 1) representation in the volume domain. Default: 1
    nslices:
        Number of slices in the volume for 3d geometries. Defaults to the height of the detector.
    algorithm: None, str, dict
        Algorithm to use for the volume reconstruction. Supported: "FP_CUDA", "BP_CUDA", "FBP_CUDA",
        "SIRT_CUDA", "SART_CUDA", "CGLS_CUDA", "EM_CUDA", "FP3D_CUDA", "BP3D_CUDA", "FDK_CUDA",
        "SIRT3D_CUDA", "CGLS3D_CUDA".
        Defaults to:
        - "FDK_CUDA" for 3d cone geometry
        - "FBP_CUDA" for 2d cone geometry (fanflat)
        - "BP3D_CUDA" for 3d parallel geometry
        - "FBP_CUDA" for 2d parallel geometry

    Example
    -------
    FDK projection and reconstruction of a phantom.

    >>> import numpy as np
    >>> from hotopy import tomo
    >>> from hotopy.datasets import balls

    >>> det_shape = height, width = (120, 128)
    >>> phantom = balls((height, width, width))
    >>> numangles = int(1.5 * width)
    >>> angles = np.linspace(0, 2 * np.pi, numangles + 1)[:-1]
    >>> # source-object dist, source-detector dist, pixelsize
    >>> z01, z02, px = 99, 100, 1

    >>> t = tomo.setup(phantom.shape[:-1], angles, cone=(z01, z02, px))
    >>> projections = t.project(phantom)

    >>> volume_reconstruction = t.reconstruct(projections)
    """
    det_shape = np.atleast_1d(det_shape)
    proj = None
    if det_shape.ndim != 1:
        proj = det_shape
        num_angles, *det_shape = proj.shape
        if num_angles != len(angles):
            raise ValueError(
                "when passing projections instead of the detector shape, the number of angles has to match"
            )
        if len(det_shape) > 2:
            raise ValueError(f"incompatible projections shape: {proj.shape}")

    use_3d = len(det_shape) == 2
    use_cone = cone is not None

    if use_3d:
        nrow = det_shape[-2]
        nslices = nslices or nrow  # use all slices if not set
        nslices = math.ceil(nslices / voxel_size)

    angles = -np.asarray(angles)  # switch to astra convention
    nx = det_shape[-1]
    if sino_pad == "corner":
        sino_pad = int(nx * (np.sqrt(2) - 1) / 2 + 1)
    elif not isinstance(sino_pad, Number):
        raise ValueError(f"Use 'corner' or a number for sino_pad ({sino_pad = })")
    ncol = nx + 2 * sino_pad  # detector width (includes padding)
    nx = math.ceil(nx / voxel_size)  # volume width (no padding)

    if use_cone:
        assert len(cone) == 3
        assert all(isinstance(x, Number) for x in cone)
        m, z01_eff, z12_eff = (par / voxel_size for par in _transform_geo_pars(*cone))

    if isinstance(algorithm, str) and not algorithm.endswith("_CUDA"):
        logger.warning("Using cpu algorithm.")

    match use_cone, use_3d:
        case True, True:
            p_geometry = astra.create_proj_geom("cone", m, m, nrow, ncol, angles, z01_eff, z12_eff)
            alg_cfg = algorithm_config(algorithm or "FDK_CUDA")
        case True, False:
            p_geometry = astra.create_proj_geom("fanflat", m, ncol, angles, z01_eff, z12_eff)
            alg_cfg = algorithm_config(algorithm or "FBP_CUDA")
        case False, True:
            # 3D FBP will be available once someone applies the filter :)
            p_geometry = astra.create_proj_geom(
                "parallel3d", 1 / voxel_size, 1 / voxel_size, nrow, ncol, angles
            )
            if algorithm is None:
                logger.warning(
                    "3d filtered backprojection is not available. defaulting to (unfiltered)\n"
                    "backprojection. Please consider using FDK with a narrow cone by setting\n"
                    "cone=(80000, 30, 1), or use the _stack functions of a 2D tomo."
                )
            alg_cfg = algorithm_config(algorithm or "BP3D_CUDA")
        case False, False:
            p_geometry = astra.create_proj_geom("parallel", 1 / voxel_size, ncol, angles)
            alg_cfg = algorithm_config(algorithm or "FBP_CUDA")
        case _:
            raise ValueError(
                f"how did you get here? are those booleans:{type(use_cone)}, {type(use_3d)}?"
            )

    if use_3d:
        v_geometry = astra.create_vol_geom(nx, nx, nslices)
        astra_tomo = AstraTomo3D(p_geometry, v_geometry, alg_cfg, sino_pad)
    else:
        v_geometry = astra.create_vol_geom(nx, nx)
        astra_tomo = AstraTomo2D(p_geometry, v_geometry, alg_cfg, sino_pad)
    if proj is not None:
        astra_tomo.set_projections(proj)
    return astra_tomo


def get_angles(geo: ProjectionGeometry) -> ndarray:
    """get angles of the ray directions projected onto a horizontal plane"""
    match geo["type"]:
        case "cone_vec":
            # src pos - det pos
            v = geo["Vectors"]
            angles = np.arctan2(v[:, 1] - v[:, 4], v[:, 0] - v[:, 3]) + np.pi / 2
        case "fanflat_vec":
            # src pos - det pos
            v = geo["Vectors"]
            angles = np.arctan2(v[:, 1] - v[:, 3], v[:, 0] - v[:, 2]) + np.pi / 2
        case "parallel3d_vec" | "parallel_vec":
            # 'ray direction'
            v = geo["Vectors"]
            angles = np.arctan2(v[:, 1], v[:, 0]) + np.pi / 2
        case _:
            try:
                angles = geo["ProjectionAngles"]
            except KeyError as e:
                raise ValueError(f"{geo['type']} not supported") from e
    return -angles  # switch sign back from astra


def get_magnifications(geo: ProjectionGeometry) -> ndarray:
    """get geometrical magnification of the sample for each projection"""
    match geo["type"]:
        case "cone_vec":
            v = geo["Vectors"]
            dist_src = np.linalg.norm(v[:, 0:3], axis=1)
            dist_det = np.linalg.norm(v[:, 3:6], axis=1)
            return (dist_src + dist_det) / dist_src
        case "fanflat_vec":
            v = geo["Vectors"]
            dist_src = np.linalg.norm(v[:, 0:2], axis=1)
            dist_det = np.linalg.norm(v[:, 2:4], axis=1)
            return (dist_src + dist_det) / dist_src
        case "parallel3d_vec" | "parallel_vec":
            return 1
        case _:
            try:
                dist_src = geo["DistanceOriginSource"]
                dist_det = geo["DistanceOriginDetector"]
                return (dist_src + dist_det) / dist_src
            except KeyError as e:
                raise ValueError(f"{geo['type']} not supported") from e


def vector_geometry(p_geometry: ProjectionGeometry) -> ProjectionGeometry:
    """Convert geometry to vector type"""
    if p_geometry["type"].endswith("_vec"):
        return p_geometry
    else:
        return astra.geom_2vec(p_geometry)


def shift_geometry(
    p_geometry: ProjectionGeometry,
    shift: ArrayLike,
    move: Literal["detector", "sample"] = "detector",
) -> ProjectionGeometry:
    """Apply shifts in a projection geometry in the detector's (fixed) orientation.

    Modify either the detector or the sample position. The shift gets interpreted dependent
    on its shape. When moving the sample, horizontal movement is to the left when looking
    with the beam, while the vertical direction goes up. When moving the detector, this is
    flipped, to achieve similar effects on the projections.

        shift.shape: interpretation
             (1,  ) : horizontal
             (2,  ) : (horizontal, vertical)
    (num_angles,  ) : horizontal per angle
    (num_angles, 2) : horizontal and vertical per angle

    The shift magnitude is specified in detector pixels when moving the detector and in
    effective pixels when moving the sample.

    Parameters
    ----------
    p_geometry: dict
        Projection geometry to apply the shifts in
    shift: ArrayLike
        The shifts are explained above.
    move: "detector" or "sample (optional)
        Whether to reposition the detector (default) or the sample.
    """
    if move not in ("sample", "detector"):
        raise ValueError('move either "detector" or "sample"')

    p_geometry = vector_geometry(p_geometry)
    V = p_geometry["Vectors"]

    # bring shift into order (angle, direction)
    shift = np.atleast_1d(shift)
    if shift.ndim == 1:
        if len(shift) == 1:  # just one horizontal shift
            shift = np.c_[shift[0], 0]
        elif len(shift) == 2:  # one horizontal and one vertical shift
            shift = shift[None, :]
        elif len(shift) == len(V):  # horizontal shifts for all angles
            shift = shift[:, None]
        else:
            raise ValueError(f"incompatible {shift.shape = }")

    # demagnify shift, when moving sample
    if move == "sample" and p_geometry["type"] in ("cone_vec", "fanflat_vec"):
        shift /= get_magnifications(p_geometry)[:, None]

    # 2d geometries
    if p_geometry["type"] in ("parallel_vec", "fanflat_vec"):
        if shift.shape[1] > 1 and np.any(shift[:, 1]):
            raise ValueError(f"no vertical shifts can be applied in a 2d geometry. shift: {shift}")
        total_shift = shift * V[:, 4:6]
        V[:, 2:4] -= total_shift  # move source
        if move == "sample" and p_geometry["type"] == "fanflat_vec":
            # in the reference frame of the sample, source and detector have to move
            V[:, 0:2] -= total_shift  # move detector
        return p_geometry

    if p_geometry["type"] not in ("parallel3d_vec", "cone_vec"):
        raise ValueError(f"geometry type {p_geometry['type']} not recognised.")

    # 3d geometries
    total_shift = shift[:, 0, None] * V[:, 6:9]
    if shift.shape[-1] > 1:
        total_shift += shift[:, 1, None] * V[:, 9:12]
    V[:, 3:6] -= total_shift  # move detector
    if move == "sample" and p_geometry["type"] == "cone_vec":
        # in the reference frame of the sample, source and detector have to move
        V[:, 0:3] -= total_shift  # move source

    return p_geometry


def rotation_matrix3d(axis: ArrayLike, theta: float) -> ndarray:
    """
    rotation matrix associated with counterclockwise rotation around
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array(
        [
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
        ]
    )


def geo_roll_rotaxis(p_geometry: ProjectionGeometry, angle_deg: ArrayLike) -> ProjectionGeometry:
    """
    Rotate the detector in beam direction (or the sample against it).
    If angle_deg is an array, it is applied per tomographic projection.
    """
    p_geometry = vector_geometry(p_geometry)

    if p_geometry["type"] not in ("parallel3d_vec", "cone_vec"):
        raise RuntimeError("No suitable geometry for geo_roll_rotaxis: " + p_geometry["type"])

    V = p_geometry["Vectors"]

    match p_geometry["type"]:
        case "parallel3d_vec":
            reverse_beam_directions = V[:, 0:3]
        case "cone_vec":
            reverse_beam_directions = V[:, 0:3] - V[:, 3:6]

    angle_deg = np.broadcast_to(angle_deg, len(V))
    for i_proj in range(len(V)):
        rot = rotation_matrix3d(reverse_beam_directions[i_proj], np.deg2rad(angle_deg[i_proj]))
        V[i_proj, 6:9] = rot @ V[i_proj, 6:9]
        V[i_proj, 9:12] = rot @ V[i_proj, 9:12]

    return p_geometry


def geo_pitch_rotaxis(p_geometry: ProjectionGeometry, angle_deg: ArrayLike) -> ProjectionGeometry:
    """
    shift and rotate source and detector corresponding to a misaligned pitch-angle
    of the rotation axis. The nick rotation is orthogonal to the beam and to z
    (3rd coordinate). When rotating by a positive pitch angle, the side of the sample
    close to the source moves down while the side close to the detector moves up.
    If angle_deg is an array, it is applied per tomographic projection.
    """
    p_geometry = vector_geometry(p_geometry)

    if p_geometry["type"] not in ("parallel3d_vec", "cone_vec"):
        raise RuntimeError("No suitable geometry for geo_pitch_rotaxis: " + p_geometry["type"])

    V = p_geometry["Vectors"]
    angle_rad = np.broadcast_to(np.deg2rad(angle_deg), len(V))
    for i_proj in range(len(V)):
        beam_direction = V[i_proj, 3:6] - V[i_proj, 0:3]
        nick_direction = np.cross(beam_direction, (0, 0, 1))
        rot_mat = rotation_matrix3d(nick_direction, angle_rad[i_proj])
        V[i_proj, 0:3] = rot_mat @ V[i_proj, 0:3]
        V[i_proj, 3:6] = rot_mat @ V[i_proj, 3:6]
        V[i_proj, 6:9] = rot_mat @ V[i_proj, 6:9]
        V[i_proj, 9:12] = rot_mat @ V[i_proj, 9:12]
    return p_geometry
