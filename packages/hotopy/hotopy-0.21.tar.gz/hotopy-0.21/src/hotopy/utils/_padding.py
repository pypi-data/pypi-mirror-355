from itertools import chain
import numpy as np
from numpy.typing import ArrayLike
import torch


def pad_width_as_pairs(pad_width, ndim):
    """Expands pad_size input to according [(before_j, after_j), ...] notation (numpy representation)."""
    # copied from numpy.lib.arraypad._as_pairs without optimizations
    pad_width = np.broadcast_to(pad_width, (ndim, 2))
    if not np.issubdtype(pad_width.dtype, np.integer):
        raise ValueError(f"pad_width needs to be an integer type (not {pad_width.dtype})")
    return pad_width.tolist()


def pad_width_to_torch(pad_width, ndim):
    """
    Converts numpy's pad_width representation to Torch representation.

    Parameters
    ----------
    pad_width
    ndim

    Returns
    -------
    tuple : torch pad_width representation
    """
    # ensure pair representation
    pad_pairs = pad_width_as_pairs(pad_width, ndim)

    # For whatever reason pad width in torch is of inverse order and in one long int-tuple (not in before, after
    # pairs as in numpy).
    # Here, we reverse pairs order and merge all into one tuple.
    return tuple(chain(*reversed(pad_pairs)))


class _PadderBase:
    def __init__(self, imshape, pad_width, mode="constant", value=0):
        self.imshape = tuple(imshape)
        self.imdim = len(imshape)
        self.pad_width = pad_width_as_pairs(pad_width, self.imdim)
        self.crop_slice = (...,) + tuple(slice(pl, -pr or None) for pl, pr in self.pad_width)

    def __call__(self, array):
        pass

    def crop(self, array):
        return array[self.crop_slice]

    @property
    def padded_shape(self):
        """Shape of padded image."""
        return tuple(s + pl + pr for s, (pl, pr) in zip(self.imshape, self.pad_width, strict=True))

    inv = crop
    """Alias for crop."""


class IdentityPadder(_PadderBase):
    def __init__(self, imshape, pad_width, **kwargs):
        super().__init__(imshape, 0, **kwargs)  # pad_width is fixed as 0

    def __call__(self, array):
        return array

    def crop(self, array):
        return array


class Padder(_PadderBase):
    """
    Pad numpy arrays and torch tensors, but also have access to invert the padding (crop).
    Parameter input aligns with numpy.pad and is translated for torch calls.

    Parameters
    ----------
    imshape: tuple
        shape of the data to be padded
    pad_width: sequence, array_like, int
        Number of values padded to the edges of each axis. See numpy.pad for details.
    mode: str
        pad mode as specified in numpy.pad. Only "constant", "edge", "wrap" and "reflect" are supported for tensors
    value:
        combines "stat_length" "constant_values", "end_values" parameters of numpy.pad.
        value for constant padding for tensors.

    Example
    -------
    >>> import numpy as np
    >>> import torch
    >>> from hotopy.utils import Padder

    >>> print(arr := np.arange(9).reshape(3, 3))
    >>> p = Padder(arr.shape, 1)
    >>> print(f"{p.padded_shape = }")
    >>> print(padded := p(arr))
    >>> print(unpadded := p.inv(padded))

    >>> print(arr := torch.as_tensor(arr))
    >>> p = Padder(arr.shape, ((2, 0), (3, 1)), mode="edge")
    >>> print(padded := p(arr))
    >>> print(unpadded := p.inv(padded))
    """

    _torch_padmode_from_numpy = {
        "edge": "replicate",
        "wrap": "circular",
    }

    def __new__(cls, imshape, pad_width, **kwargs):
        if np.any(pad_width):
            return super().__new__(cls)
        # use identity operator, when no padding is requested
        return IdentityPadder(imshape, pad_width)  # pad_width is ignored anyways

    def __init__(self, imshape, pad_width, mode="constant", value=0):
        super().__init__(imshape, pad_width, mode=mode, value=value)

        # build arguments for numpy pad calls
        self.np_args = {"mode": mode}
        match mode:
            case "constant":
                self.np_args["constant_values"] = value
            case "linear_ramp":
                self.np_args["end_values"] = value
            case "maximum" | "mean" | "median" | "minimum":
                self.np_args["stat_length"] = value

        # build arguments for torch pad calls
        self.torch_args = {
            "mode": self._torch_padmode_from_numpy.get(mode, mode),
            "value": value,
        }
        self.pad_width_torch = pad_width_to_torch(self.pad_width, self.imdim)

    def __call__(self, array):
        array_class = type(array)

        if array_class is torch.Tensor:
            # batch dimension is needed for non constant padding in torch
            padded = torch.nn.functional.pad(array[None], self.pad_width_torch, **self.torch_args)
            padded = padded[0]  # remove auxiliary batch dimension
        else:
            if array_class is not np.ndarray:
                array = np.asarray(array)

            pad_width = [[0, 0]] * (array.ndim - self.imdim) + self.pad_width
            padded = np.pad(array, pad_width, **self.np_args)

        return padded


def crop_to_shape(arr: ArrayLike, shape: tuple) -> ArrayLike:
    """
    Crops `a` symmetrically around the center to given shape `shape`. For axes with odd cropping
    one more entry gets cropped towards the end.

    Parameters
    ----------
    arr: ArrayLike
        array to crop
    shape: tuple
        output shape. Needs to be <= arr.shape in every dimension.

    Returns
    -------
        array cropped around the center with shape `shape`.

    Example
    -------
    >>> import numpy as np
    >>> from hotopy.utils import crop_to_shape

    >>> for shape, shape_out in (
    >>>     ((4, 4), (2, 3)),
    >>>     ((5, 5), (2, 3)),
    >>> ):
    >>>     arr = np.arange(np.prod(shape)).reshape(shape)
    >>>     print(arr), print(crop_to_shape(arr, shape_out))
    """
    crop = (shape_in - shape_out for shape_in, shape_out in zip(arr.shape, shape, strict=True))
    slices = tuple(slice(c // 2, -((c + 1) // 2) or None) for c in crop)

    return arr[slices]


def crop_quadratic(array: ArrayLike, dim: tuple = (-2, -1)) -> ArrayLike:
    """
    Crop images towards the center such, that all dimensions in `dim` end up having the same length.
    Where an uneven amount needs to cropped, one more element towards the end is discarded.

    Arguments
    ---------
    array: ArrayLike
        Array to be cropped.
    dim: tuple
        Dimensions where cropping is applied. Defaults to the last two dimensions.
    """
    min_size = min((array.shape[d] for d in dim))
    slices = [slice(None)] * array.ndim
    for d in dim:
        crop = array.shape[d] - min_size
        slices[d] = slice(crop // 2, -((crop + 1) // 2) or None)

    return array[tuple(slices)]
