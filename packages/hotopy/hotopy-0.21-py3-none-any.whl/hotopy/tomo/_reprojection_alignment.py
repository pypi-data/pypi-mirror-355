import numpy as np
from copy import deepcopy

from hotopy.image import register_images
from typing import Literal, Any, TypeVar, Union, Optional
from numpy.typing import ArrayLike
from collections.abc import Callable
import logging
import tqdm

from ._astra import AstraTomo3D


logger = logging.getLogger(__name__)
default_pbar = tqdm.tqdm


def idop(x: Any) -> Any:  # identity operator
    return x


State = TypeVar("State")
Gradient = Callable[[State], State]
Norm = Callable[[State], float]


class IterativeAlgorithm:
    """Algorithm structure."""

    state: State
    monitor: "Monitor"

    def __init__(self, monitor=None, max_iter=None):
        """Initialize algorithm. Set variables, parameters, stepsizes, etc."""
        self.niter = 0
        if monitor is None:
            self.monitor = Monitor(self)
        else:
            self.monitor = monitor(self)

        self.stop_conditions = {}
        self.max_iter = max_iter
        if max_iter is not None:
            self.stop_conditions["max_iter"] = self.max_iter_reached

    def stop_condition(self) -> bool:
        """Checks convergence and stopping conditions."""
        raise NotImplementedError

    def update(self):
        """Do one iteration step."""
        raise NotImplementedError

    def max_iter_reached(self):
        return self.niter >= self.max_iter

    def __call__(self):
        with self.monitor as mon:
            done = False
            while not done:
                self.niter += 1
                self.update()
                for name, condition in self.stop_conditions.items():
                    if condition():
                        print(f"stopping iteration: condition {name} has been met.")
                        done = True
                mon.observe()


class Monitor:
    def __init__(self, alg: IterativeAlgorithm) -> None:
        self.alg = alg

    def __enter__(self) -> "Monitor":
        return self

    def __exit__(self, type, value, traceback) -> None:
        return

    def observe(self) -> None:
        return


class ReprojectionMonitor(Monitor):
    def __enter__(self) -> "ReprojectionMonitor":
        assert self.alg.max_iter is not None
        # init progress bar
        self.pbar = tqdm.tqdm(total=self.alg.max_iter)
        # init state trajectory
        self.trajectory = np.empty(
            (self.alg.max_iter + 1, *self.alg.state.shape),
            self.alg.state.dtype,
        )
        self.trajectory[0] = self.alg.state
        self.convergence = np.empty(self.alg.max_iter)
        return self

    def __exit__(self, type, value, traceback):
        self.pbar.close()
        last_it = self.alg.niter + 1
        if type is not None:
            last_it -= 1
        self.trajectory = self.trajectory[:last_it]
        self.convergence = self.convergence[:last_it]

    def observe(self):
        self.pbar.update()
        self.pbar.set_description(f"norm: {self.alg.current_norm:e}")
        self.trajectory[self.alg.niter] = self.alg.state
        self.convergence[self.alg.niter - 1] = self.alg.current_norm


class QuasiGradient(IterativeAlgorithm):
    state: State
    dx: Union[State, None]
    grad: Gradient
    norm: Norm = np.linalg.norm  # convergence norm
    tol: float  # convergence tolerance

    def __init__(
        self,
        state: State,
        grad: Gradient,
        tau: float,
        norm: Optional[Norm] = None,
        tol: Union[float, None] = 0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.state = state
        self.grad = grad
        self.tau = tau
        self.dx = None

        if norm is None:
            self.norm = np.linalg.norm
        else:
            self.norm = norm
        self.tol = tol
        self.current_norm = None

        self.stop_conditions["tolerance"] = self.tolerance_reached

    def update(self):
        self.dx = self.grad(self.state)
        self.state -= self.tau * self.dx

    def tolerance_reached(self):
        if self.tol is not None and self.dx is not None:
            self.current_norm = self.norm(self.dx)
            return self.current_norm <= self.tol
        return False


def _default_convergence_norm(shifts):
    """1 px shift missmatch has as much weight as 1 deg rotation missmatch"""
    max_shift = np.linalg.norm(shifts[:, :2], axis=1).max()
    if shifts.shape[1] > 2:
        max_rot = shifts[:, 2:].max()
    else:
        max_rot = 0
    return max_shift + max_rot


class ReprojectionAlignment:
    """align tomographic projections by a reprojection approach

    The algorithm works iteratively, where each iteration is composed of three steps:
    (1) Reconstruct a 3D-object from pre-aligned projections by filtered back-projection
    (2) Simulate projections from the reconstructed 3D-object
    (3) Improve the current alignment by registering the measured with the simulated projections

    Example
    -------
    >>> from hotopy import tomo
    >>> from hotopy.datasets import balls
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt

    >>> det_shape = height, width = (120, 128)
    >>> phantom = balls((height, width, width))
    >>> numangles = 200
    >>> angles = np.linspace(0, 2*np.pi, numangles+1)[:-1]
    >>> shifts = 1.5 * (np.random.random((numangles, 2)) - 0.5) + (2, 0)
    >>> z01, z02, px = 99, 100, 1

    >>> t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
    >>> t.apply_shift(shifts)
    >>> projections = t.project(phantom)

    >>> t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
    >>> rep_al = tomo.ReprojectionAlignment(t, projections, move="detector")
    >>> rep_al.vol_constraint = tomo.Constraints(vmin=0)
    >>> found_shifts = rep_al(tol=0.1, max_iter=50, upsample=20)

    >>> plt.plot(shifts, label="ground truth")
    >>> plt.plot(found_shifts, ".",label="determined shifts")
    >>> plt.legend()

    >>> plt.figure()
    >>> vol_reco = t.reconstruct()
    >>> plt.imshow(vol_reco[vol_reco.shape[0]//2])
    """

    def __init__(
        self,
        t: AstraTomo3D,
        projections: Optional[ArrayLike] = None,
        vol_constraint: Optional[Callable[[ArrayLike], ArrayLike]] = None,
        move: Literal["detector", "sample"] = "detector",
    ) -> None:
        """
        Parameters
        ----------
        t: AstraTomo3D
            Tomography object to apply the reprojection alignment to. This should have projection data loaded.
        projections: ArrayLike (optional)
            Projection data to load before the reprojection alignment
        vol_constraint: Callable (optional)
            Volume constraint to apply during interations. hotopy.tomo.Constraints can be used to create
            a suitable Callable.
        move: "detector" (default) or "sample"
            Whether to apply the detectoed shifts to the sample or detector position
        """
        self.t = t
        self.vol_constraint = vol_constraint
        self.conv_norm = _default_convergence_norm
        self.move = move

        self.geo_in = deepcopy(t.p_geometry)
        if projections is None:
            projections = t.projections

        self.projections = t.linkable_proj_array(projections)
        self.reprojections = t.linkable_proj_array(np.empty_like(self.projections))
        self.numangles = projections.shape[0]

        angles = t.angles
        self.s = np.sin(angles)
        self.s /= np.linalg.norm(self.s)
        self.c = np.cos(angles)
        self.c /= np.linalg.norm(self.c)

    def shift_update(self, initial_shifts, upsample_factor=20):
        t = self.t

        # update geometry
        t.apply_shift(initial_shifts, move=self.move, reference_geom=self.geo_in)

        # reconstruction
        logger.debug("reconstruction")
        if t.sino_pad == 0:
            t.reconstruct(self.projections, link=True)
        else:
            t.reconstruct(self.projections)  # linking does not work with sino_pad != 0

        if self.vol_constraint is not None:
            t.apply_constraint(self.vol_constraint)

        # forward projection
        logger.debug("forward projection")
        if t.sino_pad == 0:
            t.set_projections(self.reprojections, link=True)
            t.project(get_data=False)
        else:
            self.reprojections = t.project()

        # registration
        logger.debug("shift registration")
        shifts = np.zeros((self.numangles, 2))
        for i_proj in range(self.numangles):
            shifts[i_proj, 1::-1], _ = register_images(
                self.projections[i_proj],
                self.reprojections[i_proj],
                upsample_factor=upsample_factor,
                mode="shift",
            )

        # remove shift components that correspond to a global translation of the sample
        # horizontal
        shifts[:, 0] -= (
            np.dot(self.s, shifts[:, 0]) * self.s + np.dot(self.c, shifts[:, 0]) * self.c
        )
        # vertical
        shifts[:, 1] -= shifts[:, 1].mean()

        return shifts

    def __call__(
        self,
        initial_shifts: Optional[ArrayLike] = None,
        max_iter: Union[int, None] = 10,
        tol: float = 0.1,
        upsample: Optional[float] = None,
    ):
        """
        Parameters
        ----------
        initial_shifts: ArrayLike (optional)
            Shifts to initialize the algorithm with. Has to be broadcastable to (numangles, 2).
            Default: 0
        max_iter: Union[int, None] (optional)
            Maximum number of reprojection iterations. Set to `None` for no limit. Default: 10
        tol: float (optional)
            Tolerance in the computed shifts used as a stopping criterion for the iterations:
            the iterations are stopped when the shifts change <= shiftTolerance from one iteration to the
            next for all projections. Default: 0.1
        upsample: float (optional)
            Upsampling factor for the shift registration. See skimage.correlation.phase_cross_correlation
            for details. Default: 1 / `tol`

        """
        if initial_shifts is None:
            initial_shifts = np.zeros((self.numangles, 2))
        else:
            initial_shifts = np.broadcast_to(initial_shifts, (self.numangles, 2)).copy()

        if upsample is None:
            upsample = 1 / tol

        solver = QuasiGradient(
            initial_shifts,
            lambda shift: -self.shift_update(shift, upsample_factor=upsample),
            tau=1,
            norm=self.conv_norm,
            tol=tol,
            max_iter=max_iter,
            monitor=ReprojectionMonitor,
        )
        self.solver = solver

        try:
            solver()
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt in ReprojectionAlignment.")
            print("Gathering results... To abort, please interrupt again.")

        final_shifts = solver.state
        self.t.apply_shift(final_shifts, reference_geom=self.geo_in)

        self.shifts = solver.monitor.trajectory
        self.convergence = solver.monitor.convergence

        return final_shifts
