"""
.. author: Jens Lucht
"""

import numpy as np
from scipy.special import erfc
from ..utils import fftfreqn
from .propagation import expand_fresnel_numbers


# where to properly place this function?
def erf_filter(shape, cutoff, delta, dx=1.0, dtype=None):
    """
    Error function (erf) based fourier frequency filter for n-dim FFTs ``shape`` at cutoff
    frequency ``f_cutoff` and width plus/minus ``delta``, giving an effective transition width
    of ``2 * delta``.

    This filter is designed as low-pass. The corresponding high-pass can be defined by
    ``hp = 1.0 - erf_filter(shape, f_cutoff, delta)``.

    Parameters
    ----------
    shape: tuple, int
        Dimensions of data
    cutoff: float
        Cutoff frequency, i.e. where filter has value of 0.5.
    delta: float
        Width of transition.
    dx: float, array-like
        Spacing for fftfreq.

    Returns
    -------
    tf: array
         Fourier space transfer/filter function in shape ``shape``.

         .. Note:: Returns in FFT order. See ``ifftshift``.

    Notes
    -----
    For data with different sampling per dimension, use the ``dx`` argument for scaling the frequencies accordingly.

    Example
    -------
    Simple 1-dim. error-function (erf) filter in Fourier space, for data of size 512, and cutoff at 0.3 with width 0.1
    meaning a transition

    >>> from hotopy.holo import erf_filter
    >>> n = 512
    >>> tf = erf_filter(n, 0.3, 0.1)

    Inspect filter. Note, the radially (in 1-dim y-axis) symmetry.

    >>> import matplotlib.pyplot as plt
    >>> from numpy.fft import fftfreq
    >>> plt.plot(fftfreq(n), tf)
    >>> plt.vlines([-0.3, 0.3], 0, 1, color="k")
    >>> plt.vlines([-0.4, -0.2, 0.2, 0.4], 0, 1, color="g", linestyle="--")
    >>> plt.show()


    See also
    --------
    ctf_erf_filter
    twolevel_regularization
    """
    # n-dim fourier frequency vector
    f = fftfreqn(shape, dx, dtype=dtype)
    f_norm = np.sqrt(sum(map(np.square, f)))  # modulus = sqrt(sum_i |f_i|^2)

    # transfer/filter function
    tf = 0.5 * erfc((f_norm - cutoff) / (delta / 2))

    # return in safe data type inferred by sqrt function.
    # note: erfc does not handle float16 values, returns float32 instead
    return tf.astype(f_norm.dtype)


def ctf_erf_filter(shape, fresnel_nums, f_cutoff=None, f_width=None, dtype=None):
    r"""
    Fourier frequency filter or regularization function for CTF and Fresnel near field holography.

    The main idea is to distinguish between the root at zero frequency and higher frequencies roots, since the root at
    zero cannot be treated by multi-distance scans in contrast to the higher frequencies roots. Hence, the roots of the
    (CTF) transfer function can be divided into two regimes.
    This function returns a smooth error function-based transition kernel in frequency space with transition located
    between this two regimes. Thus, the transition frequency (called cutoff frequency) defaults to the first maximum
    of the pure phase (sine-)CTF.

    This implementation supports astigmatism through Fresnel numbers per axis, i.e. per x- and y-direction.

    Parameters
    ----------
    shape: tuple
        Dimensions of image data.
    fresnel_nums: array_like, float
        (Pixel) Fresnel numbers. Supports multi-distance (in zero-th axis) and astigmatism (in first axis).
    f_cutoff: float, Optional
        Cutoff frequency. Defaults to :math:`\sqrt{\frac{F}{2}}`, frequency of the first phase-CTF maximum,
        at Fresnel number F.
    f_width: float, Optional
        Frequency width of transition. Transition starts at ``f_cutoff - f_width`` and spans to  ``f_cutoff + f_width``.
        Defaults to distance between first maximum and following first non-zero frequency root of phase (sine-)CTF, i.e.
        :math:`\sqrt{F} - \sqrt{\frac{F}{2}}`.
    dtype: dtype, Optional
        Datatype passed to ``fftfreq``.

    Returns
    -------
    kernel: array
        Filter kernel per frequency in shape ``shape``.

        .. Note:: The kernel is ordered in FFT order. See ``ifftshift``.

    See also
    --------
    erf_filter
    twolevel_regularization
    """
    fresnel_nums = expand_fresnel_numbers(fresnel_nums, shape=shape)

    # astigmatism remains in now 0-th axis, i.e. fnum.shape is (ndim,), i.e [fy, fx, ...].
    fnum = fresnel_nums.mean(0)
    # APPROXIMATION: using mean (over multi measurements) Fresnel number for regularization. This may lead to undesired
    # behavior of the regularization if large differences are present in the Fresnel numbers.
    # IMPROVEMENT: use min(0) instead

    # scalar reference Fresnel number (for astigmatism)
    F = np.min(fnum)
    # cutoff frequency at first zero of p-CTF
    f_cutoff = f_cutoff or np.sqrt(F / 2)
    # transition frequency width. Set to difference between first min-max of p-CTF, which are at sqrt(F/2) and sqrt(F)
    f_width = f_width or np.sqrt(F) * (1 - 1 / np.sqrt(2)) * np.sqrt(2)

    # handling of astigmatism: different sampling per axis, scaled to reference Fresnel num F
    sampling_ratios = fnum / F
    # Fresnel number enters square-rooted in relation to frequency
    dx = np.sqrt(abs(sampling_ratios))

    # transfer kernel or transition function based on error function in frequency space
    kernel = erf_filter(shape, f_cutoff, f_width, dx=dx, dtype=dtype)

    return kernel


def twolevel_regularization(
    shape, fresnel_nums, alpha, f_cutoff=None, f_width=None, beta=0.0, delta=1.0, dtype=None
):
    """
    Generalized 2-level regularization for Fresnel holography.

    This regularization is designed to regularize the principal zero at `|f| -> 0 (f: frequency)` of the phase CTF with
    one regularization strength and the higher roots with another strength.

    Parameters
    ----------
    shape : tuple
        Dimensions of grid to determine regularization for. Can be scalar int.
    fresnel_nums : array-like
        (Pixel) Fresnel number to scale spatial frequencies.
    alpha : tuple, float
        List with two entries ``(alpha_low, alpha_high)`` frequency dependent regularization. A single value is treated
        as constant regularization in all frequencies.
    f_cutoff: float, optional
        Cutoff frequency in Fourier space. Defaults to first maximum of phase (sine-)CTF.
    f_width: float, optional
        Width of error function-based transition. Defaults to distance between first maximum and the following root of
        phase CTF.
    beta : float, optional
        Correction of transition for coupled, homogenous objects. If `delta=1` can also be beta-delta-ratio.
    delta : float, optional
        Correction of transition for coupled homogenous objects.

    Returns
    -------
    weights: array
        Regularization strength per Fourier frequency in shape ``shape``.

        .. Note:: Returns in FFT order. See ``ifftshift``.

    See also
    --------
    ctf_erf_filter
    erf_filter
    """
    # correction of transition for homogenous object assumption
    if f_cutoff is None:
        # correct transition position based on homogeneous object assumption.
        # In the pure phase case (beta=0, delta=non-zero) this reproduces the sqrt(F/2) cutoff frequency.
        # note: arctan2 can handle case where beta is zero (delta/beta would be undefined).
        F = expand_fresnel_numbers(fresnel_nums, shape=shape).mean(0).min()
        f_cutoff = np.sqrt(F * np.arctan2(delta, beta) / np.pi)

    # transition function based on CTF
    tf = ctf_erf_filter(shape, fresnel_nums, f_cutoff=f_cutoff, f_width=f_width, dtype=dtype)

    # extract two regularization strengths
    a0, a1 = np.broadcast_to(alpha, (2,))
    # two-level transition: a0 up to f_cutoff, then a1
    weights = a0 * tf + a1 * (1.0 - tf)

    return weights
