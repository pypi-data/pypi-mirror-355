"""
Author: Jens Lucht
"""

import math
import itertools
import logging

import numpy as np
from numpy import asarray
from scipy.signal import find_peaks
from scipy.ndimage import zoom
from skimage.registration import phase_cross_correlation
from matplotlib import pyplot as plt

from ..image import (
    imshiftscale,
    imscale,
    radial_power_spectrum,
    gaussian_bandpass2_real,
    InpaintMinimalCurvature,
    GaussianBlur,
)


logger = logging.getLogger(__name__)


def check_fresnel_number(
    holos,
    fresnel_numbers=None,
    betadelta=0.0,
    num_minima=None,
    scale="lin",
    ax=None,
    figsize=(12, 4),
):
    """
    Visually check Fresnel number against expected contrast transfer function (CTF). Suitable for holographic data and optically weak samples.

    Plots radial power spectral density profile of given images ``holos`` together with expected ``fresnel_numbers``.

    Parameters
    ----------
    holos: array_like
        Holographic 2-dimensional image or list of there of.
    fresnel_numbers: float, list
        Expected Fresnel numbers. Can be scalar of list of scalar for multiple theory curves.

        .. Note:: Does not support astigmatism.
    betadelta: float, list
        Beta/delta ratio(s) to plot with theory curves. Default to ``0.0`` pure phase objects.
    num_minima: None, int
        The least number of roots of CTF function shown
    scale: 'lin', 'quad'
        Linear frequency scaling ``'lin'`` or quadratic ``'quad'``. In case of quadratic scaling, the CTF roots are equidistant, which make
        a visual check easy.
    ax: Axes
        Matplotlib Axes object to place plot in.
    figsize: tuple
        Size of figure to create to plot in. Ignored if ``ax`` is set.

    Returns
    -------
    ax: Axes
        Matplotlib axes object containing the plot.

    Examples
    -------

    >>> from hotopy.datasets import logo_holograms
    >>> from hotopy.holo import check_fresnel_number
    >>> data = logo_holograms()
    >>> bd = data["betaDelta"]
    >>> ax = check_fresnel_number(data["holograms"], data["fresnelNumbers"], betadelta=[bd, 0.5], scale="quad", num_minima=32)
    >>> ax.figure.show()
    """

    betadelta = np.atleast_1d(betadelta)
    holos = np.atleast_2d(holos)
    if holos.ndim == 2:
        holos = holos[np.newaxis]
    if fresnel_numbers is None:
        fresnel_numbers = find_fresnel_number(holos[0])[0]
        print(f"WARNING: using automatically determined fresnel numbers: {fresnel_numbers}")
        print("for better results, pass fresnel number manually")

    fresnel_numbers = np.atleast_1d(fresnel_numbers)

    if holos.ndim > 3:
        raise ValueError(
            "More than 3 dimensiones for holos not supported. Note: zero-th axis is assumed to be stack axis."
        )
    if not fresnel_numbers.ndim == 1:
        raise ValueError("Astigmatism not supported. Fresnel numbers need to be 1-dimensional list")
    if not betadelta.ndim == 1:
        raise ValueError("Betadelta values need to be 1-dimensional list or scalar")
    if scale not in ["lin", "quad"]:
        raise ValueError(f"Illegal scale value '{scale}'.")

    if num_minima is None:
        # maximal number of contained minima up to Nyquist frequency
        num_minima = math.ceil(1 / (4 * np.min(fresnel_numbers)) + np.arctan(np.max(betadelta)))

        # auto scaling
        num_minima = min(max(num_minima, 3), 25)
    num_minima = int(num_minima)

    # emit warning, if first CTF root is larger than Nyquist frequency
    if np.max(fresnel_numbers) >= 0.25:
        logger.warning(
            "Less than one CTF root expected for at least one Fresnel number, correctness of Fresnel number cannot be"
            "visually verified."
        )

    # frequency at highest minima limited to Nyquist
    cutoff = min(math.sqrt(num_minima * np.max(fresnel_numbers)), 0.5)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax.semilogy()

    # data curves
    ymax = 1e5
    ymin = 1e4
    for i, holo in enumerate(holos):
        psd, psd_freq, _ = radial_power_spectrum(holo)
        ax.plot(psd_freq, psd, label=f"hologram {i + 1}")

        i_cutoff = np.argmax(psd_freq > cutoff) or None
        ymax = max(ymax, np.max(psd[10:i_cutoff]))
        ymin = min(ymin, np.min(psd[:i_cutoff]))

    # expected theory curves for all combination of parameters
    comb = itertools.product(fresnel_numbers, betadelta)
    samples_per_minimum = 50
    for i, (fnum, bd) in enumerate(comb):
        gamma = np.arctan(bd)
        chi = np.pi * np.arange(0.0, num_minima + 1, 1 / samples_per_minimum) - gamma
        chi[chi < 0] = 0.0  # corresponds to invalid frequency range
        ctfsq = ymax * np.square(np.sin(chi + gamma))  # squared to show roots as minima
        ctfsq[::samples_per_minimum] = ymin * 1e-1  # push ctf-zeros to lower border
        xi = np.sqrt(chi * fnum / np.pi)
        ax.plot(xi, ctfsq, ls="--", lw=0.75, label=f"$|CTF|^2$ {fnum = :.2e} {bd = :.1e}")

    ax.set_ylim(ymin * 1e-1, ymax * 1e2)
    ax.set_xlim(0, cutoff)
    ax.legend(ncols=2)
    ax.set_xlabel("Frequency")

    # quadratic frequency scale
    def quad_forward(x):
        return np.square(x)

    def quad_inverse(x):
        return np.sqrt(x)

    if scale == "quad":
        ax.set_xscale("function", functions=(quad_forward, quad_inverse))
        ax.tick_params("x", rotation=60)

    return ax


def rescale_defocus_series(
    series,
    mag,
    out=None,
    upsample_factor=10,
    normalization=None,
    regargs=None,
    transformargs=None,
    sigma_gaussfilt=None,
):
    """
    Rescale measurement series of same sample at different magnifications to maximal magnification and register
    and correct shift eventually. Used in multi-distance holographic reconstructions with cone beam geometry.

    Uses DFT registration algorithm proposed in [1]_.

    Parameters
    ----------
    series : array-like
        Series of images to scale and register stacked in first axis.
    mag : array-like
        Magnifications corresponding to series of images. Needs to be array of length `series.shape[0]`.
    out : array, optional
        Output array to place corrected images in. Need to be in shape and dtype of series.
    upsample_factor : int, optional
        Upsampling factor for registration. See [2]_. Defaults to 10.
    normalization : str, None, optional
        Normalization factor used in registration step. See [2]_ and Notes below.
        Defaults to `None` which is different from skimage's default `'phase'`.
        See Notes in [2]_, this normalization should be more robust to noise.
    regargs : dict, None, optional
        Additional keyword arguments passed to `skimage.registration.phase_cross_correlation`. See Notes.
    transformargs : dict, None, optional
        Additional keyword arguments passed to `imshiftscale`.
    sigma_gaussfilt: tuple[float] or None, optional
        Apply Gaussian filtering as preprocessing before registering or ``None`` skips filtering.

    Returns
    -------
    out : array
        Stack of corrected and scaled images.
    shifts : array
        Shifts registered relative to image with maximal magnification in units of magnified image.

    Notes
    -----
    Used `skimage.registration.phase_cross_correlation` [2]_. See here for additional information and references.

    Rotations later with maybe [3]_.

    Currently, no reconstruction of holograms for better registration. Subject to change.

    Example
    -------
    >>> # example not tested ;)
    >>> from os import cpu_count
    >>> from multiprocessing import Pool
    >>> import numpy as np
    >>> from scipy.fft import set_workers
    >>> from hotopy.holo import rescale_defocus_series
    >>> # [...] load scaled but flat-field corrected holograms into `holos_raw` and corresponding magnifications into
    ... # `mag`. `holos_raw.shape = (n_theta, n_distances, pixel_x, pixel_y)`.
    >>> n_cpu = cpu_count()
    >>> set_workers(2)
    >>> n_parallel = n_cpu // 2
    >>> def parallel_rescale(holos):
    ...     # return only the corrected holograms, set more options if needed
    ...     return rescale_defocus_series(holos, mag)[0]
    >>> with Pool(n_parallel) as p:
    ...     holos = p.map(parallel_rescale, holos_raw)
    >>> holos = np.asarray(holos)

    Note, the above example is not optimized in memory usage. A more elaborated script could make use shared memory
    (e.g. from Python's `multiprocessing` module) and use the inplace variant of this method by setting the `out`
    argument.

    References
    ----------
    .. [1] Manuel Guizar-Sicairos, Samuel T. Thurman, and James R. Fienup,
           "Efficient subpixel image registration algorithms,"
           Optics Letters 33, 156-158 (2008). :DOI:`10.1364/OL.33.000156`
    .. [2] https://scikit-image.org/docs/stable/api/skimage.registration.html#phase-cross-correlation
    .. [3] https://scikit-image.org/docs/stable/auto_examples/registration/plot_register_rotation.html#sphx-glr-auto-examples-registration-plot-register-rotation-py
    """
    regargs = regargs or {}
    transformargs = transformargs or {}

    preprocess = None
    if sigma_gaussfilt is not None:
        sigmas = tuple(sigma_gaussfilt)
        if len(sigmas) != 2:
            raise ValueError("Only two sigmas (low, high) are allowed.")

        def preprocess(x):
            return gaussian_bandpass2_real(x, *sigmas)

    max_ind = np.argmax(mag)
    max_mag = mag[max_ind]
    n = len(mag)

    scales = max_mag / asarray(mag)
    ref = asarray(series[max_ind])

    # preprocess reference image
    if preprocess is not None:
        ref = preprocess(ref)

    # allocate output memory
    # temporary image needed, if output=input (i.e. inplace) since original input needed in imshiftscale again
    tmp = np.empty_like(ref)
    if out is None:  # if output not given, preallocate memory
        out = np.empty((n, *ref.shape), dtype=ref.dtype)
    shifts = np.zeros((n, ref.ndim))
    errors = np.zeros((n,))

    # scale series to common maximal magnification
    for i, (im, scale) in enumerate(zip(series, scales, strict=True)):
        if i == max_ind:
            # no need to rescale and register reference image, shifts and error remain zero
            out[i] = series[i]
        else:
            # first rescale to common scaling before applying preprocessing
            imscale(im, scale, output=tmp)

            if preprocess is not None:
                tmp = preprocess(tmp)

            # register reference image and rescaled and preprocessed image
            shifts[i], errors[i] = phase_cross_correlation(
                ref,
                tmp,
                upsample_factor=upsample_factor,
                normalization=normalization,
                **regargs,
            )[:2]

            # correct input series to maximal magnification and correct shifts eventually
            imshiftscale(im, shifts[i], scale, output=out[i], **transformargs)

    return out, shifts, errors


def rescale_defocus_fresnel_numbers(fresnel_nums, mag):
    """
    Rescales fresnel numbers accordingly to magnifications `mag`. in cone beam geometry to effective parallel beam
    setup.

    Parameters
    ----------
    fresnel_nums : array-like
        Fresnel numbers in cone beam setup
    mag : array-like
        Magnification factors

    Returns
    -------
    fresnel_nums : array
        Fresnel numbers in effective parallel beam.
    """
    mag = asarray(mag)
    fresnel_nums = asarray(fresnel_nums)
    return fresnel_nums * (mag / max(mag)) ** 2


def find_fresnel_number(
    x, prominence=0.3, flow=None, fhigh=None, guess=None, max_order=16, stats="median"
):
    """
    Fresnel number determination from given hologram ``x``.

    NOTE: Experimental function, likely to change.

    Parameters
    ----------
    x: array_like
        Hologram to determine Fresnel number of.
    prominence: float, tuple[float] or None, optional
        Required prominence of a peak. Vary this parameter to filter out false peaks (here minima). ``None`` disables
        prominence filters.
    flow: float or None, optional
        Lower frequency limit. If ``None`` and guess given, set to half of first pure phase CTF root.
    fhigh: float or None, optional
        Higher frequencies limit. If ``None`` and guess given, set to max_order-th root of pure phase CTF.
    guess: float or optional
        Initial guess for Fresnel number, used for masking of power spectrum.
    max_order: int, optional
        Cutoff after ``max_order`` pure phase (sin-)CTF roots. Only possible if ``guess`` is given.
    stats: None or str, optional
        Statistical reduction method to use: either ``'median'`` (default, equivalent to ``None``) or ``'mean'``.
        Median is more robust against outliers, mean is more robust against (slightly) peak position errors.

    Returns
    -------
    fresnel_number : float
        Determined Fresnel number
    freq_minima: array
        Frequencies of found minima.
    peak_properties: tuple
        Properties of peak.


    Example
    -------
    TODO

    Notes
    -----
    This is *not* are fire and forget function. Check your results and eventually adapt parameters to your needs.
    """
    psd, freq = radial_power_spectrum(x)[:2]

    if guess is not None:
        # lower limit to prevent noisy low-freq signal to influence too much
        flow = flow or np.sqrt(1 / 2 * guess)
        if max_order is not None:
            fhigh = fhigh or np.sqrt(max_order * guess)

    mask = np.ones_like(freq).astype(bool)
    if flow is not None:
        mask &= freq >= flow
    if fhigh is not None:
        mask &= freq <= fhigh

    y = np.log(psd[mask])
    (xp, pp) = find_peaks(-y, prominence=prominence)

    freq_xp = freq[mask][xp]
    diff = np.diff(freq_xp**2)

    if stats is None or str(stats).lower() == "median":
        fn = np.median(diff)
    elif str(stats).lower() == "mean":
        fn = np.mean(diff)
    else:
        raise ValueError("Illegal stats value. Possible values: None, 'median', or 'mean'.")

    return fn, freq_xp, pp


def fresnel_number_pairs(fresnel_num_list):
    """
    List of all two-element combinations for given list of Fresnel numbers.

    .. Note:: Does not support astigmatism.
    """
    return list(itertools.combinations(fresnel_num_list, 2))


def difference_fresnel_numbers(fresnel_nums):
    """
    Returns all possible difference Fresnel number for given Fresnel numbers ``fresnel_nums``.

    .. Note:: Does not support astigmatism.
    """

    def compute_diff_fnum(pair):
        """Compute difference Fresnel number given pair (f1, f2)"""
        f1, f2 = pair
        return 1 / abs(1 / f1 - 1 / f2)

    pairs = fresnel_number_pairs(fresnel_nums)
    return np.array(list(map(compute_diff_fnum, pairs)))


def _predict_zoom_shape(shape, factor):
    return np.rint([(si * factor) for si in shape]).astype(int)


def flatfield_inpainting_correction(
    holo, mask, sigma=None, pad=None, binning=None, order=None, mode=None, dtype=None, device=None
):
    """
    Flatfield post correction for low frequency or slowly varying background artefacts for compact supported objects.

    Parameters
    ----------
    holo: array_like
        Hologram to inpaint. Needs to be flatfield divided before.
    mask: array_like
        (Boolean) support mask, where true indicates the position of the object. Support does not need to be precise but
        shall not include parts of the "bulk object". Fine holographic fringes scattering out from the object are fine.
    sigma: float, None, Optional
        Kernel size for Gaussian low-pass filter kernel applied to hologram before inpainting. Note, here remaining
        fringes outside of the support should be smoothed out. ``None`` as default uses kernel size of 100 pixel.
    pad: None, "auto", int
        Padding size or automatic (``"auto"``) padding used to suppress edge artifacts. ``0`` disables padding at all.
    binning: int, Optional
        Binning factor to reduce image size. If not given the factor will be chosen such, that the hologram to inpaint
        is of size ``(256, 256)``.
    order: int, Optional
        Interpolation order for binning and upsampling.
    mode: str, Optional
        Edge mode for binning/upsampling.
    dtype: np.dtype, Optional
        Datatype for inpainting. If not given, datatype from holo will be used.
    device: None, torch.Device, Optional
        So far only Gaussian prefilter is applied on device.
    """
    order = order or 2
    mode = mode or "nearest"
    sigma = sigma or 100
    if pad is None:
        pad = "auto"  # by default, do nice edges

    holo = np.asarray(holo)
    # Apply Gaussian low pass filter. After filtering cast back to ndarray with .numpy()
    holo_lowpass = GaussianBlur(holo.shape, sigma, pad=pad, device=device)(holo).cpu().numpy()

    # ensure at most (256, 256) pixel to be used for inpainting for performance, if not given explicitly
    binning = binning or max(1, min(np.min(sigma) / 2, np.sqrt(holo.size / 256**2)))
    # check if zoom back recovers original shape, otherwise abort
    # TODO fix this behavior
    binned_shape = _predict_zoom_shape(holo.shape, 1 / binning)
    zommed_shape = _predict_zoom_shape(binned_shape, binning)
    if not np.all(zommed_shape == holo.shape):
        raise ValueError(
            f"Binning factor {binning:.3f} is not a divisor of the image shape {holo.shape}."
            f"Please use a different binning factor. "
        )

    holo_binned = zoom(holo_lowpass, 1 / binning, order=order, mode=mode, prefilter=False)
    mask_binned = zoom(mask, 1 / binning, order=0, mode="constant", cval=False, prefilter=False)

    dtype = dtype or holo.dtype
    inpainting = InpaintMinimalCurvature(holo_binned.shape, mask_binned, dtype=dtype, device=device)
    holo_binned, inpainting_values = inpainting(holo_binned, out=holo_binned)

    holo_inpainted = zoom(holo_binned, binning, order=order, mode=mode, prefilter=False)

    holo_corrected = holo / holo_inpainted

    return holo_corrected, holo_inpainted
