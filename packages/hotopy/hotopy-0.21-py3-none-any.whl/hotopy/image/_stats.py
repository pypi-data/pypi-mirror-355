import numpy as np
from scipy.stats import binned_statistic
from scipy.fft import fftn

from ..utils import fftfreqn
from . import ndwindow


def radial_profile(s, center=None, bin_width=1, bins=None):
    """
    Calculates the radial profile of an n-dimesional signal `s` by azimuthal averaging.

    s: array_like
        Signal to calculate the radial average of.
    center: tuple (optional)
        center in image coordinates. Defaults to the image center.

        Ignored when x is passed.
    bin_width: number (optional)
        Width of radial bins to use. Ignored, if `bins` is given. Default is 1.

        Ignored when bins are passed.
    bins: int, array_like (optional)
        If integer number of bins to use, if array defines bins to use.

        Ignored when bins are passed.

    Returns
    -------
    average: array
        mean value per radial bin
    radii: array of dtype float
        radial bin edges
    binnumber:
        indices of the bin, in which each value belongs.
    """
    s = np.asarray(s)
    shape = np.asarray(s.shape)

    if center is None:
        center = (shape - 1) / 2

    # convert pixel indices to radial distance to center
    xv = np.indices(shape) - center[..., np.newaxis, np.newaxis]
    x = np.sqrt(np.sum(np.square(xv), axis=0))

    if bins is None:
        bins = np.arange(0, x.max() + bin_width, bin_width)

    return binned_statistic(x.ravel(), s.ravel(), bins=bins)


def radial_power_spectrum(s, window=("kaiser", 8), bins=None, workers=-1):
    """
    Azimuthal averaged power spectral density of n-dimensional signal s.

    Parameters
    ----------
    s: array_like
        N-dimensinal signal `s` to compute azimuthally averaved power spectrum of.
    window: str, tuple, Optional
        Optionally apply windowing before calculation of power spectrum to suppress boundary effects. See
        scipy.signal.get_window window argument for possible values.
        Defaults to `("kaiser", 8)`. Set to `None` if no windowing should be applied.
    bins: array_like, None
        Bins to use for ``scipy.stats.binned_statistic``. ``None`` defaults to equispaced bins in range ``[0.0, 0.5]``
        in length ``max(s.shape)//2 + 1``. By suppling bins explicitly, non-uniform bins can be used.
    workers: int, None
        Number of parallel threads used for computation of the FFT. Negative values wrap around number of system cores.
        Defaults to all cores available on the system.

    Returns
    -------
    psd: array
        Azimuthally averaged power spectral density profile in length ``len(bins)``.
    freqs: array
        Central frequency of each frequency bin. Values are between ``[0.0, 0.5]``.
    binn: array
        Bin number of power spectral density.


    See Also
    --------
    ``scipy.stats.binned_statistic``

    Example
    -------
    >>> psd, freq, binn = radial_power_spectrum(im, ("kaiser", 8))
    """
    s = np.asarray(s)
    shape = s.shape

    if window is not None:
        s = s * ndwindow(window, shape)

    S = fftn(s, workers=workers)
    psd = np.square(abs(S))

    # compute distance of frequency from zero frequency on fft grid
    freqs = fftfreqn(shape, sparse=True)
    x = np.sqrt(sum(map(np.square, freqs)))

    # compute azimuthal average
    if bins is None:
        bins = np.linspace(0.0, 0.5, max(shape) // 2 + 1)
    rpsd, edges, binn = binned_statistic(x.ravel(), psd.ravel(), bins=bins)

    # compute central frequencies from bin edges
    rpsd_freq = (edges[:-1] + edges[1:]) / 2

    return rpsd, rpsd_freq, binn


def fourier_shell_correlation(im1, im2, window=None, dfreq=None):
    """
    Fourier shell correlation (FSC) of n-dim inputs im1 and im2.

    Parameters
    ----------
    im1, im2: array-like
        n-dimensional images to compute the FSC of.
    window: (optional)
        Apply windowing before calculation of fourier transform to suppress boundary effects.
        See scipy.signal.get_window window argument for possible values.
        Defaults to `("kaiser", 8)`. Set to False if no windowing should be applied.
    dfreq: float (optional)
        Stepsize of the frequency sampling in cycles / pixel
    get_res: bool (optional)
        Whether to determine and return the half_bit frequency (where `fsc` drops below `half_bit`)

    Returns
    -------
    freq:
        Frequency shells in cycles / pixel (bin centers).
    fsc:
        Fourier shell correlation corresponding to the frequencies in freq.
    nfreq:
        Number of (fft) sample points per shell in Fourier space.
    half_bit:
        Half-bit threshold curve. See :Heel_JSB_2005: for details.
    freq_half_bit:
        Frequency, where `fsc` first drops below the `half_bit` curve. See :Heel_JSB_2005: for details.

    Example
    -------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> import scipy.misc
    >>> image = scipy.misc.face()[:,:,2]
    >>> im1 = image + 500*np.random.random(image.shape)
    >>> im2 = image + 500*np.random.random(image.shape)
    >>> freq, fsc, nfreq, half_bit, freq_hb = fourier_shell_correlation(im1, im2)
    >>> plt.plot(freq, fsc, label='FSC')
    >>> plt.plot(freq, half_bit, label='half-bit threshold')
    >>> plt.axvline(freq_hb, label='resolution cut-off')
    >>> plt.xlabel('frequency / (cycles / pixel)')
    >>> plt.legend()
    """
    if window in (None, True):
        window = ("kaiser", 8)

    def preprocess(im):
        im = np.asarray(im)
        if window is not False:
            im = im * ndwindow(window, im.shape)
        return im

    f1 = fftn(preprocess(im1))
    f2 = fftn(preprocess(im2))

    # determine frequency bins
    shape = np.asarray(f1.shape)
    ndim = len(shape)
    if dfreq is None:
        dfreq = 1 / shape.min()
    freq = np.arange(0, 0.5 * np.sqrt(ndim), dfreq)  # requested sampling
    freq_grid = np.sqrt(sum([xi * xi for xi in fftfreqn(shape)]))
    bins = np.digitize(freq_grid, (freq[1:] + freq[:-1]) / 2)

    # results
    nfreq = np.bincount(bins.ravel(), minlength=len(freq))

    nominator = np.bincount(
        bins.ravel(), weights=(f1.real * f2.real + f1.imag * f2.imag).ravel(), minlength=len(freq)
    )
    denom1 = np.bincount(
        bins.ravel(), weights=(f1.real * f1.real + f1.imag * f1.imag).ravel(), minlength=len(freq)
    )
    denom2 = np.bincount(
        bins.ravel(), weights=(f2.real * f2.real + f2.imag * f2.imag).ravel(), minlength=len(freq)
    )
    fsc = nominator / np.sqrt(denom1 * denom2)

    half_bit = half_bit_threshold(nfreq, ndim)

    # determine half-bit-frequency
    i_max = int(np.argwhere(fsc < half_bit)[0, 0])
    slc = slice(i_max - 1, i_max + 1)
    freq_half_bit = np.interp(0, np.flip(fsc[slc] - half_bit[slc]), (freq[i_max], freq[i_max - 1]))

    return freq, fsc, nfreq, half_bit, freq_half_bit


def half_bit_threshold(nfreq, ndim):
    """
    Half-bit threshold curve for the Fourier shell correlation [1]_.

    Parameters
    ----------
    nfreq: ArrayLike:
        number of frequency voxels per shell
    ndim: int
        number of dimensions

    References
    ----------
    .. [1]
        v. Heel, M., Schatz, M. (2005). Fourier shell correlation threshold criteria. Journal of Structural Biology, 151-3, pp.250-262, 1047-8477.
        :doi:`10.1016/j.jsb.2005.05.009`
    """
    return (0.2071 + 1.9102 / nfreq ** (1 / (ndim - 1))) / (
        1.2071 + 0.9102 / nfreq ** (1 / (ndim - 1))
    )
