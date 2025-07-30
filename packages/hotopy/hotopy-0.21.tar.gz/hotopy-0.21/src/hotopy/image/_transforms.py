import numpy as np
from numpy import ones, diag, asarray, ascontiguousarray, ndarray
from numpy import linalg
from scipy.ndimage import affine_transform, shift as ndshift
from torch.nn import AvgPool2d
from torch.nn.functional import affine_grid, grid_sample
from torch import Tensor, as_tensor, view_as_real, view_as_complex
import torch
from collections.abc import Sequence
from numpy.typing import ArrayLike
from ..utils import expand_to_dim
from functools import wraps


def imscale(input, scale, center=True, mode="nearest", **kwargs):
    """
    Scales an image using an affine transformation.

    See `scipy.ndimage.affine_transform` [1]_.

    Parameters
    ----------
    input : array
        Array to zoom.
    scale : float, tuple
        Scale factor per dimension or scalar if same along all directions.
    center : bool, optional
        Zoom into center of the image. Defaults to `True`, *which is different from `affine_transform` standard
        behavior*.
        Set offset argument to zoom into different regoins in the array.
    mode : str, optional
        Change default value of affine_transform to `'nearest'`.
    **kwargs: optional
        any keyword argument affine_transform supports

    Returns
    -------
    Scaled image with same shape as entered image `im`.

    Notes
    -----
    Scaling or maginfication of an image is different than zooming (in scipy's sense)
    as when scaled the shape of the image does not change, if zoomed, e.g. with
    `scipy.ndimage.zoom` the shapes does change.

    Example
    -------
    >>> from hotopy.image import imscale
    >>> from scipy.misc import ascent
    >>> im = ascent()
    >>> zoomin = imscale(im, 2)
    >>> zoomout = imscale(im, (1/2, 1))

    References
    ----------
    .. [1] https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.affine_transform.html#scipy-ndimage-affine-transform
    """
    # early exit, if there is nothing to do
    if scale == 1:
        return input

    if center and "offset" in kwargs and kwargs["offset"] is not None:
        raise ValueError(
            "Conflicting arguments passed to function: explicit offset and auto-centering are mutually exclusive."
        )
    offset = kwargs.pop("offset") if "offset" in kwargs else None

    input = ascontiguousarray(input)
    scale = scale * ones(input.ndim)

    # inverse of affine transformation matrix needs to be passed to affine_transform. Inverse of "diagonal" elements
    # or diagonal matrix is equal.
    inv = 1 / scale

    # zoom into center
    if center:
        offset = asarray(input.shape) / 2 * (1 - inv)

    return affine_transform(input, inv, offset=offset, mode=mode, **kwargs)


def imshift(input, shift, mode="nearest", **kwargs):
    """
    Wrapper for `scipy.ndimage.shift` with different edge behavior default of `'nearest'`.

    Parameters
    ----------
    input : array
        Array to shift.
    shift : array
        Shifts per dimension.

    Return
    ------
    shift : array
        Shifted and interpolates image.
    """
    return ndshift(input, shift, mode=mode, **kwargs)


def _center_offset(shape, scale):
    return asarray(shape) / 2 * (1 - 1 / asarray(scale))


def imshiftscale(input, shift, scale, center=True, offset=None, mode="nearest", **kwargs):
    """
    Jointly shifts and scales an array (i.e. image) using only one interpolation step.
    This should avoid image degradation if done in consecutive operations.

    Internaly an affine transformation using homogeneous coordinates is set up. See `scipy.ndimage.affine_transform`
    [1]_ and [2]_ for further details.

    Parameters
    ----------
    input : array
        Array to scale.
    shift : float, tuple
        Shift per dimension or scalar if same along all directions.
    scale : float, tuple
        Scale factor per dimension or scalar if same along all directions.
    center : bool, optional
        Zoom into center of the image. Defaults to `True`, *which is different from `affine_transform` standard
        behavior*.
        Set offset argument to zoom into different regoins in the array.
    offset : float or sequence, optional
        Offset to perform scale operations on. If `center=True` offset is determined from center!
    mode : str, optional
        Change default value of affine_transform to `'nearest'`.
    **kwargs: optional
        any keyword argument affine_transform supports

    Returns
    -------
    array
        Scaled and shifted image in same shape as `input`.

    Notes
    -----
    Use `imscale` or `imshift` if only one operation is to perform to exploit more efficient algorithms eventually.

    Scaling or maginfication of an image is different than zooming (in scipy's sense)
    as when scaled the shape of the image does not change, if zoomed, e.g. with
    `scipy.ndimage.zoom` the shapes does change.

    Example
    -------
    >>> from hotopy.image import imshiftscale
    >>> from scipy.misc import ascent
    >>> im = ascent()
    >>> transformed = imshiftscale(im, [50, -20.25], 1.25, mode="reflect")

    References
    ----------
    .. [1] https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.affine_transform.html#scipy-ndimage-affine-transform

    .. [2] https://en.wikipedia.org/wiki/Homogeneous_coordinates

    .. [3] https://en.wikipedia.org/wiki/Affine_transformation#Image_transformation
    """
    ndim = input.ndim

    # scaling along each axis (diagonal matrix) in homogeneous coordinates
    scale = scale * ones(ndim)
    scale_op = ones(ndim + 1)
    scale_op[:-1] = scale
    op = diag(scale_op)

    # translations/shifts with offset to center
    offset = offset or 0
    if center:
        offset = _center_offset(input.shape, scale)
    op[:-1, -1] = shift * ones(ndim) - asarray(offset) * scale

    # TODO add rotations?

    # inverse transformation needs to be passed to affine_transform
    inv = linalg.inv(op)

    return affine_transform(input, inv, mode=mode, **kwargs)


def affine_transform2D(
    image_stack: ArrayLike,
    shift: ArrayLike = (0, 0),
    rotate: float = 0,
    magnify: float = 1,
    mode="bilinear",
    padding_mode="border",
    inv: bool = False,
    keep_type: bool = True,
) -> Tensor:
    """
    The transformations are applied in the following order:
    (1) magnification
    (2) rotation
    (3) shift

    Note: The datatype is cast to float for the interpolation. Unless `keep_type` is set to
    `False`, it is then changed back to the input datatype.

    Note: Despite the name, shearing is not supported.

    Parameters
    ----------
    image_stack: ArrayLike
        Image(s) to be transformed. Single images (H x W) or image stacks (N x H x W) and both real and complex datatypes are supported.
        For the interpolation, the datatype (of the real and imaginary part) will be cast to float.
    shift: ArrayLike
        Shift: (vertical, horizontal). Default: (0, 0)
    rotate: float
        Rotation around the image center in degrees. Default: 0
    magnifiy: float
        Magnification. Default: 1
    mode: "bilinear" | "nearest" | "bicubic"
        Interpolation mode. Default: "bilinear"
    padding_mode: "border" | "zeros" | "reflection"
        Padding mode. Default: "border"
    inv: bool
        Whether the inverse transformation should be applied instead. Default: False
    keep_type: bool
        When set to True (default), the data is cast back to its original datatype after the transformation.
    Returns
    -------
    transformed: Tensor
        transformed image(s)
    """
    imshape = image_stack.shape[-2:]
    if image_stack.ndim not in (2, 3):
        raise ValueError("Only single images (H x W) or image stacks (N x H x W) are supported")
    extra_dim = 3 - image_stack.ndim
    image_stack = as_tensor(image_stack).view((1, -1, *imshape))

    dtype_in = image_stack.dtype
    if dtype_in.is_complex:
        image_stack = view_as_real(image_stack)
        image_stack = image_stack.permute(0, 1, 4, 2, 3).reshape(1, -1, *imshape)

    image_stack = image_stack.to(dtype=float)

    rotate *= np.pi / 180
    s, c = np.sin(rotate), np.cos(rotate)
    s0, s1 = (-shift[i] * 2 / imshape[i] for i in (0, 1))
    m = magnify
    if not inv:
        trafo_matrix = as_tensor(
            [
                [
                    [c / m, -s / m, s1],
                    [s / m, c / m, s0],
                ]
            ]
        )
    else:
        trafo_matrix = as_tensor(
            [
                [
                    [c * m, s * m, -m * (c * s1 + s * s0)],
                    [-s * m, c * m, -m * (-s * s1 + c * s0)],
                ]
            ]
        )

    grid = affine_grid(trafo_matrix, image_stack.shape, align_corners=False)
    transformed = grid_sample(
        image_stack, grid, mode=mode, padding_mode=padding_mode, align_corners=False
    )

    if dtype_in.is_complex:
        transformed = transformed.reshape(1, -1, 2, *imshape).permute(0, 1, 3, 4, 2)
        transformed = view_as_complex(transformed.contiguous())

    if keep_type:
        transformed = transformed.to(dtype=dtype_in)

    return transformed[(0,) + extra_dim * (0,)]


@expand_to_dim(3)
def to_polar2D(image: ArrayLike, r: Sequence | None = None, phi: Sequence | None = None) -> Tensor:
    """
    transforms image to polar coordinates.

    Parameters
    ----------
    image: ArrayLike
        Image of shape (H x W) or image stack of shape (N x H x W)
    r: Sequence
        Radial coordinates for the output grid. Default:

    Returns
    -------
    result: Tensor
        Transformed image in polar coordinates.
        For default radial and angular coordinates see parameters `r` and `phi`.

    Example
    -------
    >>> import matplotlib.pyplot as plt
    >>> from hotopy.datasets import checkerboard
    >>> from hotopy.image import to_polar2D
    >>> plt.imshow(to_polar2D(checkerboard((256, 256), 16)))
    """
    image = as_tensor(image, dtype=torch.float32)
    assert image.ndim == 3
    min_shape = min(image.shape[-2:])
    if r is None:
        r = torch.linspace(0, 1, min_shape // 2).view(-1, 1)
    if phi is None:
        phi = torch.linspace(0, 2 * torch.pi, 2 * min_shape + 1)[:-1].view(1, -1)
    grid_polar = torch.stack(
        [
            r * torch.cos(phi),
            r * torch.sin(phi),
        ],
        dim=2,
    )
    result = grid_sample(image[None], grid_polar[None], align_corners=False)[0]
    return result


class AveragePool2d:
    @wraps(AvgPool2d.__init__)
    def __init__(self, *args, **kwargs) -> None:
        self.filter = AvgPool2d(*args, **kwargs)

    @expand_to_dim(3, n=1)
    def __call__(self, images: ArrayLike) -> ndarray:
        return self.filter(as_tensor(images)[None])[0].numpy()
