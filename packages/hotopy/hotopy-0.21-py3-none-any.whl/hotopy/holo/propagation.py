"""
======================================================
Propagation submodule (:mod:`hotopy.holo.propagation`)
======================================================

Numerical propagation methods for holographic X-ray imaging. Here a subset of propagations methods needed mainly for
phase retrieval algorithms is implemented. For more versatile propagators we refer to our
`Python package fresnel <https://gitlab.gwdg.de/irp/fresnel>`_.

Propagators
-----------

.. autosummary::
    :toctree: generated/

    FresnelTFPropagator
    simulate_hologram


Helpers
-------

.. autosummary::
    :toctree: generated/

    expand_fresnel_numbers
    get_fresnel_critical_sampling
    check_fresnelTF_sampling
    phase_chirp

..
    author: Jens Lucht
"""

import logging
import numpy as np
import math
import torch
from torch import conj, real, exp, square, as_tensor, is_complex
from torch.fft import fftn, ifftn

from ..utils import fftfreqn, rfftfreqn, Padder

logger = logging.getLogger(__name__)


__all__ = [
    "expand_fresnel_numbers",
    "phase_chirp",
    "FresnelTFPropagator",
    "simulate_hologram",
]


def expand_fresnel_numbers(fresnel_nums, *, ndim=None, shape=None):
    """
    Returns normalized representation for Fresnel numbers per measurement per direction, to support astigmatism.

    Parameters
    ----------
    fresnel_nums : float, array
        Fresnel numbers. Special case 1-dim array (aka lists): these are treated as multiple measurements. A single
        astimatistic measurement needs to have shape ``(1, ndim)`` i.e. ``[[fy, fx]]`` for Fresnel numbers that differ
        in x- and y-direction.
    ndim : int, None, Optional
        Dimension of images.
    shape : tuple, None Optional
        Alternatively to ``ndim`` the shape of the data can be provided.

    Returns
    -------
    fresnel_nums: array
         Fresnel numbers in shape ``(n, ndim)`` with n number of distances and ndim image dimensions.

    Raises
    ------
        ValueError: if incompatible Fresnel numbers are entered.
    """
    if ndim is None and shape is None:
        raise ValueError("Either ndim or shape must be provided.")
    if shape is not None:
        shape = tuple(np.atleast_1d(shape))

    if ndim is None and shape is not None:
        ndim = len(shape)
    elif ndim is not None and shape is not None and ndim != len(shape):
        # verify ndim and len(shape) are compatible
        raise ValueError(f"Length of shape ({len(shape)}) and ndim ({ndim}) are not equal.")
    # else: only ndim is not None -> nothing to do

    fresnel_nums = np.atleast_1d(fresnel_nums)
    m = len(fresnel_nums)

    if fresnel_nums.ndim == 1:
        fresnel_nums = fresnel_nums[..., np.newaxis]
    return np.broadcast_to(fresnel_nums, (m, ndim))


def get_fresnel_critical_sampling(fresnel_nums) -> int:
    r"""
    Return critical sampling condition for given pixel Fresnel number(s).

    This functions returns the minimal sampling points required in any dimensions. It is,

    .. math:: \frac{1}{\min_i F_{(i)}},

    where :math:`F_{(i)}` it the Fresnel number in the i-th axis.

    Parameters
    ----------
    fresnel_nums: float, array_like

    Returns
    -------
    sampling: int
        Minimal required sampling for given Fresnel number(s).
    """
    return math.ceil(1 / np.min(fresnel_nums))


def check_fresnelTF_sampling(shape, fresnel_nums):
    """
    According to Zhang (TODO)
    """
    # sufficient sampling in all axes?
    return min(shape) >= get_fresnel_critical_sampling(fresnel_nums)


def phase_chirp(shape, fresnel_nums, real=False, ndim=None, dtype=None):
    # WORKAROUND
    type_maps = {
        torch.float16: np.float16,
        torch.float32: np.float32,
        torch.float64: np.float64,
        None: np.float32,  # default fallback
    }
    if dtype is None or isinstance(dtype, torch.dtype):
        try:
            np_dtype = type_maps[dtype]
        except KeyError as e:
            raise ValueError(
                f"phase_chirp: dtype {dtype} is not supported. Allowed dtypes are {type_maps.keys()}"
            ) from e
    else:
        np_dtype = np.dtype(dtype)

    shape = tuple(np.atleast_1d(shape))
    ndim = ndim or len(shape)
    fresnel_nums = expand_fresnel_numbers(fresnel_nums, ndim=ndim).astype(np_dtype)
    m = len(fresnel_nums)
    ndim_expand = ndim * (np.newaxis,)
    if isinstance(shape, int):
        shape = (shape,)

    if real:
        xi = rfftfreqn(shape, dtype=np_dtype)
        shape = (*shape[:-1], xi[-1].shape[-1])  # last axis got smaller
    else:
        xi = fftfreqn(shape, dtype=np_dtype)
    chirp = np.zeros((m, *shape), dtype=np_dtype)
    for i, freq in enumerate(xi):
        chirp += np.pi * np.square(freq) / fresnel_nums[(..., slice(None), i) + ndim_expand]

    return chirp


class _FourierConvolutionPropagator:
    @property
    def kernel(self):
        """Propagation kernel."""
        return self._kernel

    @kernel.setter
    def kernel(self, val):
        self._kernel = as_tensor(val, device=self.device)

    def __init__(
        self,
        shape,
        fresnel_numbers,
        npad=1,
        pad_width=None,
        pad_mode=None,
        dtype=None,
        device=None,
        keep_type=True,
    ):
        self.shape = tuple(shape)
        self.dtype = dtype
        self.device = device
        self._keep_type = keep_type
        self._ndim = len(shape)
        if np.isscalar(fresnel_numbers):
            # switch, if propagated field should be squeezed aka returned without auxiliary first axis.
            self._squeeze_output = True
            self._ndist = 1
        else:
            self._squeeze_output = False
            self._ndist = len(fresnel_numbers)
        self._fresnel_numbers = expand_fresnel_numbers(fresnel_numbers, ndim=self._ndim)

        if pad_width is None:
            # symmetric padding if npad option is set and no pad_width passed
            pad_size = np.ceil(np.multiply(self.shape, npad - 1)).astype(int)
            pad_width = tuple([(s_i // 2, (s_i + 1) // 2) for s_i in pad_size])
        if pad_mode is None:
            pad_mode = "constant"  # zero padding
        self.padding = Padder(self.shape, pad_width, mode=pad_mode)
        self._pad_shape = self.padding.padded_shape

        self._kernel = None
        self._init_kernel()

    def _init_kernel(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} needs to implement _init_kernel method (or this class is not intended to be"
            f"instanced directly."
        )

    def _fftn(self, x):
        # zero-pad to self._pad_shape (if needed) and FFT transform last self._ndim (= len(self.shape)) axes.
        return fftn(x, s=self._pad_shape)

    def _ifftn(self, x):
        return ifftn(x, s=self._pad_shape)

    def to_device(self, device):
        """Moves propagator to given device, e.g. GPU or back to CPU."""
        self.device = device
        self._kernel = self._kernel.to(device=device)

    def __call__(self, u0):
        u0_type = type(u0)

        u0_pad = as_tensor(self.padding(u0), device=self.device)
        U0 = self._fftn(u0_pad)
        U1 = self.kernel * U0
        u1_pad = self._ifftn(U1)
        u1 = self.padding.crop(u1_pad)

        if self._keep_type and u0_type is np.ndarray:
            out = u1.cpu().numpy()
        else:
            out = u1
        if self._squeeze_output:
            return out[0]
        return out

    def inverse(self, u0):
        """
        Inverse propgation of wavefield u0.
        Inverse propagation corresponds to complex-conjugation of the kernel.

        Notes
        -----
        If padding is used (i.e. npad != 1) the inverse is *not* an exact inverse! In the cropping step signal may get
        lost and thus the propagation not unitary anymore.
        """
        orig_kernel = self._kernel
        self._kernel = conj(self._kernel)
        u1 = self(u0)
        self._kernel = orig_kernel
        return u1


class FresnelTFPropagator(_FourierConvolutionPropagator):
    """
    Callable Fresnel transfer function propagator.

    Parameters
    ----------
    shape : tuple
        Dimension of image to propagate.
    fresnel_numbers: float, array_like
        Pixel Fresnel number(s) encoding the propagation distance, wavelength and detector pixel size.
    npad: int, float, Optional
        Padding factor, defaults to ``1``, i.e. no padding. Only used if ``pad_width = None``.
    pad_width: tuple, Optional
        Alternatively amount of padding per axis in NumPy notation. Defaults to ``None`` no padding.
    pad_mode: str, Optional
        Padding mode. See NumPy ``np.pad`` modes. Defaults to ``None`` which is zero padding.
    dtype: torch.dtype, Optional
        Real data type to use for propagation kernel.
    keep_type: bool
        If NumPy array is given, also returns NumPy if set. Defaults to ``True``. If ``False`` always a PyTorch tensor
        is returned on device given by device argument.

    Returns
    -------
    F: Callable
        Propagator, callable with ``F(x)`` to propagator ``x``.
    """

    def _init_kernel(self):
        # verify sufficient padding
        if not check_fresnelTF_sampling(self._pad_shape, self._fresnel_numbers):
            n_min = get_fresnel_critical_sampling(self._fresnel_numbers)
            logger.warning(
                UserWarning(
                    f"{self.__class__.__name__}: "
                    f"Insufficient sampling for requested Fresnel numbers. "
                    f"Use at least {n_min} sampling points in all axes. "
                )
            )

        self.kernel = np.exp(
            -1j * phase_chirp(self._pad_shape, self._fresnel_numbers, dtype=self.dtype)
        )


def simulate_hologram(
    h,
    fresnel_nums,
    betadelta=0.0,
    linear=False,
    npad=1,
    pad_width=None,
    pad_mode=None,
    propagator=None,
    device=None,
    dtype=None,
    keep_type=True,
):
    """
    Simulates hologram(s) for given (real or complex) projected refractive index image h for given (pixel) Fresnel
    numbers using the Fresnel transfer function propagator, if not given explicitly.

    Parameters
    ----------
    h : array, Tensor
        Projected refractive index image. Real part is the projected phase shift image, imaginary part the projected
        absorption image. Accepts real inputs and applies homogenous object approximation if betadelta > 0 given.
    fresnel_nums : float, array_like
        Pixel Fresnel number(s) encoding the propagation step.
    betadelta: float
        Optional. For homogenous objects projects phase shift and attenuation are proportional, with proportionality
        constant betadelta.
    linear: bool, Optional
        Switch to do linear simulation, i.e. with same assumption of optically thin object as in CTF phase
        reconstruction. Default to ``False`` nonlinear.
    npad: int, float, Optional
        Padding factor, defaults to ``1``, i.e. no padding. Only used if ``pad_width = None``.
    pad_width: tuple, Optional
        Alternatively amount of padding per axis in NumPy notation. Defaults to ``None`` no padding.
    keep_type: bool
        If NumPy array is given, also returns NumPy if set. Defaults to ``True``. If ``False`` always a PyTorch tensor
        is returned on device given by device argument.

    Example
    -------
    >>> from hotopy.datasets import dicty
    >>> from hotopy.holo import simulate_hologram
    >>> fresnel_nums = 8e-4
    >>> holo = simulate_hologram(dicty(), fresnel_nums, betadelta=2e-3, npad=2)
    """
    h_type = type(h)
    h = as_tensor(h, device=device)
    shape = h.shape

    if propagator is None:
        propagator = FresnelTFPropagator(
            shape,
            fresnel_nums,
            pad_width=pad_width,
            npad=npad,
            pad_mode=pad_mode,
            dtype=dtype,
            device=device,
        )
    elif not callable(propagator):
        raise ValueError("Propagator needs to be callable.")

    if not is_complex(h):
        h = h * (1j + betadelta)
    elif betadelta != 0.0:
        raise ValueError("Complex h and betadelta != 0 are mutually exclusive options.")

    if linear:
        g = 1 + 2 * real(propagator(h))
    else:
        u0 = exp(h)
        u1 = propagator(u0 - 1) + 1
        g = square(abs(u1))

    if keep_type and h_type is np.ndarray:
        return g.cpu().numpy()
    return g
