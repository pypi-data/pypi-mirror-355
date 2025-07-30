import numpy as np
from skimage.registration import phase_cross_correlation

from ..image import GaussianBandpass


def hlcc(g, k, L=1.0):
    """
    Calculate Helgason-Ludwig consistency condition (HLCC) moments for parallel beam geometry for orders given in k for
    given sinogram g. Supports single slice and multi-slices in g.

    g: array_like
        sinogram data in `(nangles, [nrows,] npixel)`
    k: int, array-like of ints
        order or list of orders to calculate.
    L: float
        width of detector. Defaults to unit-less length 1.

    Returns
    -------
    np.array: Moments in shape `(k_max, nangles, [nrows,])`. The last axis of g is integrated out.
    """
    k = np.asarray(k)
    npx = g.shape[-1]  # number of pixels per row
    s = np.linspace(-0.5, 0.5, npx) * L
    sk = s[..., None] ** k

    return np.inner(sk.T, g)


def _find_closest(arr, val):
    delta = abs(arr - val)

    # find first closest element
    min_indx = np.argmin(delta)
    min_val = arr[min_indx]

    return min_indx, min_val


def find_sample_rotaxis_shift(projs, thetas, atol=8.7e-4, upsample_factor=20):
    """
    Determine shift of the rotation axis from given tomogram projs and angles thetas.

    .. Note::
        This methods assumes the rotation axis to be aligned (or known) to the detector and corrects misplacement
        of a sample.

    Parameters
    ----------
    projs: array_like
        Projection images (in same order as thetas)
    thetas: array_list, list
        Tomographic angles in radians corresponding to projs.
    atol: float
        Absolute tolerance (radians) below which closeness to pi is considered as accurate (Default: below 8.7e-4 rad
        aka 0.05 deg)
    upsample_factor: int
        Upsampling factor for phase_cross_correlation.
    """
    thetas = np.asarray(thetas)

    ang0_indx, ang0 = _find_closest(thetas, 0.0)
    ang180_indx, ang180 = _find_closest(thetas, np.pi)

    if not np.isclose([ang0, ang180 - np.pi], 0.0, atol=atol).all():
        raise ValueError("Dataset does not contain 0 and 180 degree images within given tolerance.")

    img0 = projs[ang0_indx]
    img180 = projs[ang180_indx]
    return sample_rotaxis_shift_correlation(img0, img180, upsample_factor=upsample_factor)


def sample_rotaxis_shift_correlation(
    ref, turned, sigma_low=4, sigma_high=40, upsample_factor=20, normalization=None
):
    """
    Determine shift of the rotation axis from given reference projection ref and 180 degree rotated projection turned.

    .. Note::
        This methods assumes the rotation axis to be aligned (or known) to the detector and corrects misplacement
        of a sample.
    """
    if sigma_low is None and sigma_high is None:

        def prefilter(x):
            return x

    else:
        bandpass = GaussianBandpass(ref.shape, sigma_low, sigma_high)

        def prefilter(x):
            return bandpass(x).cpu().numpy()

    ref_filtered = np.atleast_2d(prefilter(ref))  # explicitly convert to ndarray
    turned_filtered = np.fliplr(np.atleast_2d(prefilter(turned)))

    shift, err, _ = phase_cross_correlation(
        ref_filtered,
        turned_filtered,
        upsample_factor=upsample_factor,
        normalization=normalization,
    )

    axis_shift = np.zeros(2, dtype=shift.dtype)
    axis_shift[0] = shift[0]
    axis_shift[1] = -shift[1] / 2.0

    return axis_shift, err


def register_sinogram(sino, upsample_factor=2, normalization=None, **kwargs):
    """
    determine angular range and global shift of a (360 deg) sinogram by
    detecting the shift between its first and second half.
    Consider using a bandpass filter on the sinogram first.

    Parameters
    ----------
    sino : 2d array-like (num_angles x detector_width)
        sinogram.
    upsample_factor : int (optional, default: 2)
        upsampling for the phase_cross correlation.
    normalization : None or "phase" (optional, default: None)
        normalization for the phase_cross correlation.
    kwargs: (optional)
        further keyword arguments are passed to phase_cross_correlation.

    Returns
    -------
    (angular_range, global_shift):
        angular_range:
            angular scan range (in rad) corresponding to the registered shift
        global_shift:
            distance of the rotation center from the sinogram center

    """
    kwargs["upsample_factor"] = upsample_factor
    kwargs["normalization"] = normalization

    num_angles = sino.shape[0]
    shift, _, _ = phase_cross_correlation(
        sino[: num_angles // 2], np.fliplr(sino[-(num_angles // 2) :]), **kwargs
    )

    # explicit casting to float to get rid of numpy datatypes
    angular_range = float(2 * np.pi * num_angles / (num_angles - 2 * shift[0]))
    global_shift = float(-0.5 * shift[1])

    return angular_range, global_shift
