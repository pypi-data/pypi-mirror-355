from typing import Optional
from itertools import repeat
import numpy as np
from numpy.typing import ArrayLike
import torch.fft
from collections.abc import Iterable
import torch
from torch import as_tensor
from scipy.signal import get_window
from scipy.fft import fft2, ifft2, rfft2, irfft2
from scipy.ndimage import fourier_gaussian
from numbers import Number
from itertools import pairwise
from collections.abc import Sequence, Callable
from typing import Literal
import math

from ..utils import rfftshape, rfftfreqn, Padder


def _broadcast_to_dim(i):
    """
    Returns indices to broadcast to dimension i, i.e. indexing operation like [...,(i-times newaxis)]
    """
    return (...,) + tuple(repeat(np.newaxis, i))


def ndwindow(window, shape):
    """
    n-dim window of scipy.signal.get_window function.

    Parameters
    ----------
    window: str or tuple
        window type to use. See scipy.signal.get_window.
    shape: tuple
        Shape of window.

    Returns
    -------
    Window in shape `shape`.
    """
    w = np.ones(shape, dtype=np.float64)
    for dim, size in enumerate(reversed(shape)):
        w *= get_window(window, size)[_broadcast_to_dim(dim)]
    return w


def gaussian_filter(im, sigma, workers=None):
    r"""
    Apply Fourier Gaussian filter on im with size sigma (in pixel units).

    Cut-off frequency :math:`D_0` is related by:
        .. math:: \sigma = (2 \pi D_0)^{-1}.

    Notes
    -----
    Does *not* broadcast to stack of images. Needs to be applied by each image individually. E.g. with `multiprocessing`:
    """
    filt = fourier_gaussian(
        fft2(im, workers=workers), sigma
    )  # sigma = 1/(2*np.pi*D0), cut-off freq
    return ifft2(filt, workers=workers).real


def gaussian_bandpass2_real(x, sigma_low=None, sigma_high=None, workers=-1):
    # early exit if nothing is to do ...
    if sigma_low is None and sigma_high is None:
        return x

    rshape = rfftshape(x.shape)
    shape = x.shape
    kernel = np.ones(rshape, dtype=x.dtype)

    if sigma_high is not None:
        kernel = 1 - fourier_gaussian(kernel, sigma_high, n=x.shape[-1])
    if sigma_low is not None:
        kernel = fourier_gaussian(kernel, sigma_low, n=x.shape[-1])

    return irfft2(rfft2(x, s=shape, workers=workers) * kernel, s=shape, workers=workers)


class FourierFilter:
    @property
    def kernel(self):
        return self._kernel

    @kernel.setter
    def kernel(self, val):
        self._kernel = as_tensor(val, device=self.device, dtype=self.dtype)

    def set_padding(self, val):
        self._pad = val
        self._padder = Padder(self.input_shape, val, mode="edge")
        self._padded_shape = self.padder.padded_shape

    @property
    def pad(self):
        return self._pad

    @property
    def padded_shape(self):
        return self._padded_shape

    @property
    def padder(self):
        return self._padder

    def __init__(self, shape, *args, real=True, norm=None, dtype=None, device=None, pad=0):
        self.input_shape = shape
        self.real = real  # use rfft?
        self.norm = norm  # fft normalization
        self.dtype = dtype
        self.device = device

        self._pad = None
        self._padder = None
        self._padded_shape = None
        self.set_padding(pad)

        if real:
            self.kernel_shape = rfftshape(self.padded_shape)
        else:
            self.kernel_shape = self.padded_shape

        self._kernel = None
        self._init_kernel(*args)

    @classmethod
    def apply(
        cls,
        data: ArrayLike,
        *args,
        ndim: Optional[int] = None,
        dtype: Optional[torch.dtype] = None,
        device: Optional[torch.device] = None,
        **kwargs,
    ):
        """
        Create the filter and directly apply it to the data.

        Parameters
        ----------
        data: ArrayLike
            data to be filtered
        ndim: int (optional)
            The filter gets applied in the last ndim dimensions of the data array. Default: all dimensions
        dtype: torch.dtype (optional)
            Datatype
        device: torch.device (optional)
            Torch device, e.g. "cpu", "cuda:0" or 0.
        *args, **kwargs:
            Arguments for the constructor of the chosen filter.

        Returns
        -------
        filtered_data: torch.Tensor
            The filtered data.

        Example
        -------
        >>> from hotopy import image
        >>> import numpy as np
        >>> import matplotlib.pyplot as plt
        >>> data = np.random.random((10, 56, 56), dtype=np.float32)
        >>> filtered_data = image.GaussianBandpass.apply(data, 5, 50, ndim=2)
        >>> plt.imshow(filtered_data[:, filtered_data.shape[1] // 2])
        """
        data = as_tensor(data, dtype=dtype, device=device)
        dtype = data.dtype
        device = data.device

        if ndim is None:
            shape = data.shape
        else:
            shape = data.shape[-ndim:]

        this_filter = cls(shape, *args, dtype=dtype, device=device, **kwargs)
        return this_filter(data)

    def _fft(self, x):
        if self.real:
            return torch.fft.rfftn(x, s=self.padded_shape, norm=self.norm)
        return torch.fft.fftn(x, s=self.padded_shape, norm=self.norm)

    def _ifft(self, x):
        if self.real:
            return torch.fft.irfftn(x, s=self.padded_shape, norm=self.norm)
        return torch.fft.ifftn(x, s=self.padded_shape, norm=self.norm)

    def _init_kernel(self, kernel):
        self.kernel = kernel

    def __call__(self, x):
        """
        Apply filter to given image or stack of images.

        Parameters
        ----------
        x: Tensor, array_like
            Image(s) to filer. A stack of images need to be in shape ``(n, *s)`` where s is the ``shape`` argument of
            constructor call.

        Returns
        -------
        Tensor:
            Filtered image as Tensor. If NumPy ndarray is required, call ``.numpy()``.
        """
        x = as_tensor(x, device=self.device)
        x = self.padder(x)
        X = self._fft(x)
        Y = X * self.kernel
        y = self._ifft(Y)
        return self.padder.crop(y)

    def __mul__(self, other):
        """multiple FourierFilters can be combined by multiplication"""
        if isinstance(other, FourierFilter):
            assert self.norm == other.norm
            new_kernel = self.kernel * other.kernel
            return FourierFilter(
                self.input_shape,
                new_kernel,
                real=self.real,
                norm=self.norm,
                device=self.device,
                pad=self.pad,
            )
        return NotImplemented

    def __imul__(self, other):
        if isinstance(other, FourierFilter):
            assert self.norm == other.norm
            self.kernel *= other.kernel
        else:
            self.kernel *= other
        return self

    __rmul__ = __mul__


class GaussianBlur(FourierFilter):
    def __init__(self, shape, sigma, pad=0, **kwargs):
        if isinstance(pad, str) and pad == "auto":
            pad = math.ceil(3 * sigma)
        super().__init__(shape, sigma, pad=pad, **kwargs)

    def _init_kernel(self, sigma):
        if self.real:
            n = self.padded_shape[-1]  # length of signal before real FFT
        else:
            n = -1  # complex FFT

        self.kernel = fourier_gaussian(np.ones(self.kernel_shape), sigma, n=n)


class GaussianBandpass(FourierFilter):
    """
    Gaussian band-pass Fourier filter.

    Multiplies the input image (or image-stack) with the Fourier transform of a Gaussian in Fourier space.

    Parameters
    ----------
    shape: tuple
        Shape of image(s) to be filtered. Without padding and without (optional) batch dimension.
    sigma_low: float, tuple
        Standard deviation of Gaussian used for kept lower frequencies. Supports standard deviation per axis given as
        tuple. See ``scipy.ndimage.fourier_gaussian`` for details.
    sigma_high: float, tuple
        Standard deviation of Gaussian used for blocked lower frequencies. Supports standard deviation per axis given as
        tuple. See ``scipy.ndimage.fourier_gaussian`` for details.

        .. Note::
            The high pass kernel is generated from the low pass by taking 1 - lowpass-kernel, i.e. swapping of
            blocked and passed frequencies.
    real: bool
        Input signal/image is real-valued (Default ``True``). If signal is complex, set ``False``.
    norm: None, str
        Normalization of FFT. Choices are ``"backward"`` or ``None``, i.e. the default, ``"forward"``, or ``"ortho"``
    dtype: torch.dtype
        datatype for the filter kernel.
    pad: int, tuple (optional)
        padding to be applied before applying the filter.
        accepts arguments like ``pad_width`` of ``numpy.pad``. Defaults to 0.

    Example
    -------
    >>> from hotopy.image import GaussianBandpass
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> image_stack = np.random.random((3, 64, 64)) + np.linspace(0, 2, 64)[None,:,None]
    >>> sigma = 1
    >>> pad = int(4 * sigma + 1)
    >>> # pad = 0  # comparison without padding
    >>> lowpass = GaussianBandpass(image_stack.shape[-2:], sigma, None, pad=pad)
    >>> highpass = GaussianBandpass(image_stack.shape[-2:], None, 2 * sigma, pad=pad)
    >>> bandpass = GaussianBandpass(image_stack.shape[-2:], sigma, 2 * sigma, pad=pad)
    >>> plt.subplot(221); plt.imshow(image_stack[0])
    >>> plt.subplot(222); plt.imshow(lowpass(image_stack)[0])
    >>> plt.subplot(223); plt.imshow(highpass(image_stack)[0])
    >>> plt.subplot(224); plt.imshow(bandpass(image_stack)[0])
    """

    def __init__(self, shape, sigma_low, sigma_high, pad=0, **kwargs):
        if isinstance(pad, str) and pad == "auto":
            pad = math.ceil(3 * sigma_low)
        super().__init__(shape, sigma_low, sigma_high, pad=pad, **kwargs)

    def _init_kernel(self, sigma_low, sigma_high):
        if self.real:
            n = self.padded_shape[-1]  # length of signal before real FFT
        else:
            n = -1  # complex FFT

        kernel = np.ones(self.kernel_shape)
        if sigma_high is not None and sigma_high != float("inf"):
            kernel = 1 - fourier_gaussian(kernel, sigma_high, n=n)
        if sigma_low is not None and sigma_low != 0:
            kernel = fourier_gaussian(kernel, sigma_low, n=n)

        self.kernel = kernel


def _ntuple(x, n):
    if isinstance(x, Iterable):
        return tuple(x)
    return tuple(repeat(x, n))


class MedianFilter2d:
    """
    Fast median filter useful for small kernel sizes. Allows GPU computations.

    Uses reflective padding at the edges. Unlike scipy.ndimage.median_filter,
    the reflective padding does not copy the edge pixels and the bias of the median for even
    kernel sizes is towards smaller numbers.

    Parameters
    ----------
    kernel_size: int | Sequence (optional)
        Kernel size for the median filter. Can be specified per image dimension. For even kernel sizes, the median is not unique
        and the lower of the two medians is used. Default: 5
    device : torch.device | None (optional)
        Compute device to perform reconstruction on. Defaults to `None` (no change of current device). Use `'cuda'` for CUDA based GPU
        computations or integer of GPU-card index, if multiple are present.

    Returns
    -------
    f: Callable
        Callable filter ``f(x)`` that can be applied on image ``x``.
    """

    def __init__(self, kernel_size, device=None):
        self.device = device
        self.median_filter = _MedianPool2d(kernel_size=kernel_size, same=True)

    def __call__(self, image):
        add_dims = 4 - image.ndim
        return self.median_filter(as_tensor(image[(None,) * add_dims], device=self.device))[
            (0,) * add_dims
        ]


class _MedianPool2d:
    """Median pool (usable as median filter when stride=1) module.

    Args:
         kernel_size: size of pooling kernel, int or 2-tuple
         stride: pool stride, int or 2-tuple
         padding: pool padding, int or 4-tuple (l, r, t, b) as in pytorch F.pad
         same: override padding and enforce same padding, boolean
    """

    def __init__(self, kernel_size=3, stride=1, padding=0, same=False):
        self.k = _ntuple(kernel_size, 2)
        self.stride = _ntuple(stride, 2)
        self.padding = _ntuple(padding, 4)  # convert to l, r, t, b
        self.same = same

    def _padding(self, x):
        if self.same:
            ih, iw = x.size()[2:]
            if ih % self.stride[0] == 0:
                ph = max(self.k[0] - self.stride[0], 0)
            else:
                ph = max(self.k[0] - (ih % self.stride[0]), 0)
            if iw % self.stride[1] == 0:
                pw = max(self.k[1] - self.stride[1], 0)
            else:
                pw = max(self.k[1] - (iw % self.stride[1]), 0)
            pr = pw // 2
            pl = pw - pr
            pb = ph // 2
            pt = ph - pb
            padding = (pl, pr, pt, pb)
        else:
            padding = self.padding
        return padding

    def __call__(self, x):
        x = torch.nn.functional.pad(x, self._padding(x), mode="reflect")
        x = x.unfold(2, self.k[0], self.stride[0]).unfold(3, self.k[1], self.stride[1])
        x = x.contiguous().view(x.size()[:4] + (-1,)).nanmedian(dim=-1)[0]
        return x


def dissect_levels(im, *lims, xp=None):
    """
    Dissect an image into sub-images containing only values from -inf <= lim1 < ... < limN < +inf

    Parameters
    ----------
    im: array
        Image
    *lims: float, Optional
        Limit values to dissect at. If no limits are given, the original image is returned with one additional axis
        prepended.
    xp: array_namespace
         Numpy, PyTorch, etc.

    Returns
    -------
    segments: array
        Dissected sub-images in shape ``(len(lims) + 1, *im.shape)``. I.e. for one limit this is ``(2, *im.shape)``.
    """
    xp = np if xp is None else xp

    lims = sorted(lims) + [float("+inf")]
    lower = float("-inf")

    masks = xp.zeros((len(lims), *im.shape), dtype=bool)

    for i, upper in enumerate(lims):
        masks[i] = (lower <= im) & (im < upper)
        lower = upper

    return im * masks


def _step_transition(x):
    return x >= 0.5


def _cos_transition(x):
    return 0.5 * (1 - np.cos(np.pi * x))


def _planck_transition(x):
    res = np.empty_like(x)
    res[x <= 0] = 0
    res[x >= 1] = 1
    mask = np.logical_and(x > 0, x < 1)
    with np.errstate(over="ignore"):
        res[mask] = 1 / (1 + np.exp(1 / x[mask] + 1 / (x[mask] - 1)))
    return res


def split_freqs(
    image: ArrayLike,
    freqs: int | Sequence,
    pad: int = 0,
    trans_func: Literal["planck", "cos", "step"] | Callable = "planck",
):
    """
    Split an image into a stack of images, among which the frequency components are distributed.
    Each image in the stack corresponds to frequencies close to one requested frequency `freq[i]`

    Parameters
    ----------
    image: ArrayLike
        Image
    freqs: int | Sequence
        Frequencies to split the image into. A weighting specified by the transition function is applied to
        frequency components between the specified `freqs` to sort them into the neighboring bins.
    pad: int, optional
        Padding to apply to the image before applying the frequency filter.
    trans_func: Literal["planck", "cos", "step"] | Callable, optional
        Transition function for the frequency weighting between `freq`s. Maps values from [0, 1] to [0, 1].
        Default: "planck" (1 / np.exp(1 / x + 1 / (x - 1)))

    Returns
    -------
    segments: array
        Dissected sub-images in shape ``(len(lims) + 1, *im.shape)``. I.e. for one limit this is ``(2, *im.shape)``.
    """
    match trans_func:
        case "planck":
            trans_func = _planck_transition
        case "cos":
            trans_func = _cos_transition
        case "step":
            trans_func = _step_transition

    if isinstance(freqs, Number):
        num_freqs = freqs
        if num_freqs == 2:
            freqs = np.array((0, 1 / np.sqrt(2)))
        else:
            n = max(image.shape)
            # freqs = (0, 1/n, ..., 1/2) * np.sqrt(2)
            freqs = np.r_[
                0, np.exp(np.linspace(np.log(1 / n), np.log(1 / 2), num_freqs - 1))
            ] * np.sqrt(2)
    else:
        freqs = np.atleast_1d(freqs)

    padder = Padder(image.shape, pad, mode="edge")

    kx, ky = rfftfreqn(padder.padded_shape)
    kr = np.sqrt(kx**2 + ky**2)
    k_weights = np.zeros((len(freqs), *kr.shape))

    # add weights for frequency transitions
    for i_interval, (freq_pre, freq_post) in enumerate(pairwise(freqs)):
        mask = np.logical_and(kr > freq_pre, kr <= freq_post)
        k_weights[i_interval + 1, mask] = trans_func((kr[mask] - freq_pre) / (freq_post - freq_pre))
        k_weights[i_interval, mask] = 1 - k_weights[i_interval + 1, mask]

    # add remaining frequencies to outermost bins
    if freqs[0] > 0:
        k_weights[0, kr <= freqs[0]] = 1
    if freqs[-1] < 1 / np.sqrt(2):
        k_weights[0, kr >= freqs[-1]] = 1

    # apply fourier filter
    im_fft = rfft2(padder(image))
    filtered_stack = padder.inv(irfft2(k_weights * im_fft[None]))

    return filtered_stack


def remove_outliers(
    image: ArrayLike,
    filtered_image: Optional[ArrayLike] = None,
    kernel_size: int = 5,
    tolerance: float = 5,
    *,
    inplace: bool = False,
    get_mask: bool = False,
    device=None,
):
    """remove hot and cold pixels and inf/nan pixels from an image.

    Replaces pixels that differ significantly between an image and its smoothed version.
    The threshold for the difference to be considered significant is
    `tolerance * std(filtered_image - image)`

    Parameters
    ----------
    image: ArrayLike
        Image to be filtered.
    filtered_image: ArrayLike | None, (optional)
        Image after applying a smoothing filter. Replacement pixels are taken from this array. The default is obtained by
        applying a median filter to image.
    kernel_size: int (optional)
        Kernel size of the default (median) image filter. Is ignored, if filtered image is passed directly. Default: 5.
    tolerance: float (optional)
        Threshold for when to consider pixels as outliers. Use a small value to filter more pixels. Default: 5
    inplace: bool (optional)
        Whether to replace the data inplace or copy it (default).
    get_mask: bool (optional)
        Whether to return the mask of updated pixels.
    device: torch device (optional)
        Torch device for the image filter. Use "cpu" or "cuda" for CPU/GPU computation. Ignored, when filtered_image is set.

    Example
    -------
    >>> from hotopy.image import remove_outliers
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt

    >>> shape = (200, 200)
    >>> num_hot_pixels = int(np.product(shape) / 1e2)
    >>> rng = np.random.default_rng(seed=1234)
    >>> image = rng.normal(1, 1, shape).astype(np.float32)
    >>> hot_pixels = np.array([rng.integers(s, size=num_hot_pixels) for s in shape])
    >>> image[(*hot_pixels,)] += 20 * rng.random(num_hot_pixels)

    >>> filtered = remove_outliers(image)

    >>> plt.subplot(121); plt.imshow(image)
    >>> plt.subplot(122); plt.imshow(filtered)
    """
    # filter image
    if filtered_image is None:
        median_filter = MedianFilter2d(kernel_size=kernel_size, device=device)
        filtered_image = median_filter(image).cpu().numpy()

    # determine output array
    out = np.array(image, copy=not inplace)

    # fix nan and inf
    non_finite_mask = ~np.isfinite(out)
    out[non_finite_mask] = filtered_image[non_finite_mask]

    # difference between original and filtered image
    difference_image = out.astype(float) - filtered_image
    std = np.std(difference_image, axis=(-2, -1), keepdims=True)

    # fix hot and cold pixels
    outlier_mask = np.abs(difference_image) > tolerance * std
    out[outlier_mask] = filtered_image[outlier_mask]

    if get_mask:
        return out, outlier_mask
    return out
