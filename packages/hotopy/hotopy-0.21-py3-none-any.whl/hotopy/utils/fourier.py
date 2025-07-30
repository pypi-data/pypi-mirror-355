"""
==============================================================
Fourier transform and space tools (:mod:`hotopy.holo.fourier`)
==============================================================


.. autosummary::
    :toctree: generated/

    ZoomFFTN
    fftfreqn
    ffrgridn
    rfftfreqn
    fftflip


..
    author: Jens Lucht, 2024
"""

from typing import Union, Tuple, List
import numbers

import numpy as np
from numpy import ndarray, meshgrid, stack
from scipy.fft import fftfreq, rfftfreq
from scipy.signal import ZoomFFT
import torch

newaxis = None


class ZoomFFTN:
    """
    N-dimensional ZoomFFT.

    See scipy.signal.ZoomFFT for details.

    Example
    -------

    Verify with "classical" n-dim FFT ``fftn``

    >>> import numpy as np
    >>> from scipy.fft import fftn
    >>> y = np.random.rand(5,4,6)  # some random shape
    >>> Y = fftn(y)
    >>> zfftn = ZoomFFTN(y.shape, 2)  # 2 corresponds to "normal" FFT case
    >>> Yz = zfftn(y)
    >>> np.allclose(Yz, Y)
    True

    Compare with zero-padded n-dim FFT to ZoomFFT into lower frequencies

    >>> Y_up = fftn(y, s=np.multiply(3, y.shape))  # upsample by zero-padding factor 3
    >>> zfftn_up = ZoomFFTN(y.shape, 2/3)  # compute at frequencies up to 2/3, a third of the full unit circle (2).
    >>> Yz_up = zfftn_up(y)
    >>> np.allclose(Yz_up, Y_up)
    True
    """

    def __init__(self, shape, fn, m=None, *, fs=2.0, endpoint=False):
        """
        Parameters
        ----------
        shape: tuple
            Dimension of data to ZoomFFT.

            .. Note:: All dimensions of an array will be Fourier transformed. No stacking or skipping of axes possible.
        fn: float, tuple, tuple[tuple]
            Frequency range(s). Supports the formats are:
             - ``fs``        -- scalar, meaning ``[0, fs)`` in all axes;
             - ``(f1, f2)``  -- 2-tuple, meaning ``[f1, f2)`` in all axes;
             - ``((f1_1, f2_1), ..., (f1_n, f2_n))`` -- N-2-tulple, defining the range per axis.
        m: ``None``, int, tuple, Optional
            Number of points to evaluate. Defaults to the value of shape (equal to ``None``).
        fs: float, Optional
            The sampling frequency. Defaults to `2` which corresponds to the FFT-like behavior.
        endpoint: bool
            Include interval limit of fn in ranges? Defaults to False. Cannot be set per axis.
        """
        try:
            shape = tuple(shape)
        except TypeError as err:
            raise ValueError(
                f"Invalid format for shape {shape} given to {self.__class__.__name__}. Only tuples are supported."
            ) from err

        self.ndim = ndim = len(shape)  # n-dim
        # handling of different cases for fn
        if isinstance(fn, numbers.Integral):
            # special treatment for scalar case since it would broadcast in all cases.
            fn = (fn,) * ndim  # n-tuple of fn
        else:
            try:
                fn = np.broadcast_to(fn, ndim)
            except ValueError:
                try:
                    fn = np.broadcast_to(fn, (ndim, 2))
                except ValueError as err:
                    raise ValueError(
                        f"Invalid format for fn ({fn}) given to {self.__class__.__name__}. See SciPy ZoomFFT."
                    ) from err

        m = np.broadcast_to(m, ndim)  # can broadcast `None` value
        fs = np.broadcast_to(fs, ndim)

        self.shape = shape
        self.fn = fn
        self.m = m
        self.endpoint = endpoint

        self._zfft = tuple(
            [
                ZoomFFT(n_i, fn_i, m=m_i, fs=fs_i, endpoint=endpoint)
                for n_i, fn_i, m_i, fs_i in zip(shape, fn, m, fs, strict=True)
            ]
        )

    def __call__(self, x):
        x = np.asarray(x)
        if x.shape != self.shape:
            raise ValueError(
                f"Dimension of data {x.shape} does not match initialization of {self.__class__.__name__} with shape"
                f" {self.shape}."
            )

        X = x

        # transform real to Fourier space axis by axis
        for i in range(self.ndim):
            X = self._zfft[i](X, axis=i)

        return X

    def points(self):
        return tuple([zfft_i.points() for zfft_i in self._zfft])

    def freqs(self, indexing="ij"):
        pts = self.points()
        fv = [zfftfreq_from_points(pts_i) for pts_i in pts]
        return np.meshgrid(*fv, indexing=indexing)


def zfftfreq_from_points(pts):
    return np.angle(pts) / (2 * np.pi)


def _meshdim(mesh):
    """Number of dimensions of meshdim (if sparse or not)."""
    if isinstance(mesh, tuple):
        return len(mesh)
    return mesh.shape[0]


def fftfreqn(n, dx=1.0, sparse: bool = True, indexing: str = "ij", dtype=None):
    """
    Return the nd Discrete Fourier Transform sample frequencies.

    Parameters
    ----------
    n : int or tuple of ints
        Window lengths.
    dx: float or tuple floats, optional (Default = 1.0)
        Sample spacings.
    sparse: bool, Optional
        Return spare meshgrid. Default to True.
    indexing: str, Optional
        Indexing scheme to use. Valid choices `'ij'` or `'xy'`. Default `'ij'`.
    dtype: dtype, Optional
        (Numpy) datatype to cast freq in. WARNING: This does not increase precision as only the result is cast.

    Returns
    -------
    xi1, xi2, ..., xin : ndarray or tuple if sparse

    See Also
    --------
    scipy.fft.fftfreq
    """
    n = np.atleast_1d(n)
    dx = np.broadcast_to(dx, n.shape)

    xi = [fftfreq(n_i, d_i).astype(dtype) for n_i, d_i in zip(n, dx, strict=True)]

    return meshgrid(*xi, sparse=sparse, indexing=indexing)


def rfftfreqn(n, dx=1.0, sparse: bool = True, indexing: str = "ij", dtype=None):
    """
    Return the nd Discrete Fourier Transform sample frequencies.

    Parameters
    ----------
    n : int or tuple of ints
        Window lengths.
    dx: float or tuple floats, optional (Default = 1.0)
        Sample spacings.
    sparse: bool, Optional
        Return spare meshgrid. Default to True.
    indexing: str, Optional
        Indexing scheme to use. Valid choices `'ij'` or `'xy'`. Default `'ij'`.
    dtype: dtype, Optional
        (Numpy) datatype to cast freq in. WARNING: This does not increase precision as only the result is cast.

    Returns
    -------
    xi1, xi2, ..., xin : ndarray or tuple if sparse

    See Also
    --------
    scipy.fft.fftfreq
    """
    n = np.atleast_1d(n)
    dx = np.broadcast_to(dx, n.shape)

    xi = [fftfreq(n_i, d_i).astype(dtype) for n_i, d_i in zip(n[:-1], dx[:-1], strict=True)]
    xi.append(rfftfreq(n[-1], dx[-1]).astype(dtype))

    return meshgrid(*xi, sparse=sparse, indexing=indexing)


def fftgridn(
    n: Tuple[int],
    dx: Union[float, List[float], ndarray] = 1.0,
    axis: int = 0,
    dtype=None,
    out=None,
):
    """FFT-Frequency grid

    Stacks :fftfreqn: in specified axis. Note, this does not support sparse arrays.

    Parameters
    ----------
    See fffreqn

    axis : Int, optional
        Dimension to stack in. Default first dimension.
        The get the freq-vector per space position, use `axis=-1` (last axis).

    """
    return stack(fftfreqn(n, dx=dx, dtype=dtype, sparse=False), axis=axis, out=out)


def rfftshape(n: Tuple[int]):
    n = np.atleast_1d(n)
    n[-1] = n[-1] // 2 + 1
    return tuple(n)


def fftflip(x, axes=None, xp=None):
    """
    Flip positive and negative frequency components on an FFT transformed array x. In particular, the Nyquist-frequency
    (zero) remains, higher frequencies are exchanged with their sign-conjugated counterpart. Note, for signals with even
    length, the highest frequency magnitude does not have a counterpart and remains unchanged.

    Parameters
    ----------
    x: array_like
        Array in Fourier space to flip.

        .. Note:: Assumes array to be in FFT order, i.e. the output of an FFT call.
    axes: tuple, None, Optional
        Axes of FFT transform. If ``None``, an `fftn`` over all axes is assumed.
    xp: array_namespace, None, Optional
        Array namespace, e.g. ``numpy`` or ``torch``.

        If ``None`` and input is a PyTorch tensor, a PyTorch tensor will be returned, otherwise unless ``xp`` is
        explicitly set, a NumPy array will be returned.

    Returns
    -------
    x_flip: array_like
        Frequency flipped array of x.

    Example
    -------
    >>> from numpy.fft import fftfreq
    >>> s4 = fftfreq(4)
    >>> f4 = fftflip(s4)
    >>> print(s4)
    [ 0.    0.25 -0.5  -0.25]
    >>> print(f4)
    [ 0.   -0.25 -0.5   0.25]
    >>> s5 = fftfreq(5)
    >>> f5 = fftflip(s5)
    >>> print(s5)
    [ 0.   0.2  0.4 -0.4 -0.2]
    >>> print(f5)
    [ 0.  -0.2 -0.4  0.4  0.2]
    """
    # fake array api
    # note: improve using proper array_namespace function
    if xp is None:
        if isinstance(x, torch.Tensor):
            xp = torch
        else:
            xp = np

    # use of torch.as_tensor required instead of `asarray` to keep `requires_grad` attr
    x = torch.as_tensor(x) if xp is torch else xp.asarray(x)

    if axes is None:
        axes = tuple(range(x.ndim))
    else:
        axes = tuple(np.atleast_1d(axes))
    # torch specific: length of shifts and axes need to align
    return xp.roll(xp.flip(x, axes), [1] * len(axes), axes)


def mesh_normalization_(freq, normalization, out=0):
    """Radially normalizes input (for sparse input)

    Parameters
    ----------
    out : Tensor, float, optional
        Pre-allocated output for summation over dimension. Use broadcast-able object.
    """
    ndim = _meshdim(freq)
    d_newaxis = (newaxis,) * ndim  # d-times newaxis tuple
    for i in range(ndim):
        out += freq[i] ** 2 / normalization[(..., slice(None), i) + d_newaxis]
    return out


def mesh_normalization(freq, normalization, out=None):
    """Radially normalizes input"""
    d = _meshdim(freq)  # dimension of space

    # slicing operator s to expand tensor to (m, d, *shape)
    d_newaxis = (newaxis,) * d  # d-times newaxis tuple
    s = (
        ...,
        slice(None),
        *d_newaxis,
    )  # == [..., :, d * newaxis]

    # expand and sum-reduction in dim
    chi = freq**2 / normalization[s]
    # reduce d-dim from (..., m, d, x, y) to (..., m, x, y)
    return chi.sum(-d - 1)
