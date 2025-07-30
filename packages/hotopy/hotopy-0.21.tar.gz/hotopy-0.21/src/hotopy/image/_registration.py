from numpy import asarray
import torch
from torch import as_tensor
from torch.fft import fft2, fftshift, ifftshift
from typing import Tuple, Literal
from collections.abc import Callable
from numpy.typing import ArrayLike
import logging
from hotopy.utils import crop_to_shape
from hotopy.image import to_polar2D, affine_transform2D
from skimage.registration import phase_cross_correlation


logger = logging.getLogger(__name__)


def _register_rot(
    im_ref: ArrayLike,
    im_mov: ArrayLike,
    upsample_factor: float = 10,
    normalization=None,
) -> float:
    """only registers rotations around the image center"""
    images = torch.stack((as_tensor(im_ref), as_tensor(im_mov)))

    images = to_polar2D(images).numpy()
    # TODO: maybe apply linear weighting (prop to sample points per frequency shell)
    shift = phase_cross_correlation(
        images[0], images[1], normalization=normalization, upsample_factor=upsample_factor
    )[0]
    rot_deg = -360 * shift[-1] / images.shape[-1]
    if shift[0] > 1:
        logger.warning(
            f"Significant radial shift detected ({shift[0]}). "
            f"The determined rotation angle is probably inaccurate. ({rot_deg})"
        )
    return rot_deg


def _fft2_center(arr, dim=(-2, -1)):
    return fftshift(fft2(ifftshift(arr, dim=dim), dim=dim), dim=dim)


def register_images(
    im_ref: ArrayLike,
    im_mov: ArrayLike,
    mode: Literal["shift", "rot", "shift_rot"] = "shift",
    upsample_factor: float = 10,
    normalization: None | Literal["phase"] = None,
    window: Callable | None = None,
) -> Tuple[Tuple[float], float]:
    """determine shift and rotation between two images.

    The registration works in two steps:
      - First, the frequency magnitude spectra of both images are determined and transformed to polar
        coordinates. Finding the shift between them using phase cross correlation yields the rotation angle.
      - After rotating `im_mov` by the determined rotation angle, the shift can be determined, again using
        phase cross correlation.
    See skimage.registration.phase_cross_correlation for details on the shift registration.

    Note:  The found shift and rotation can be plugged into `affine_transform2D`, to transform
        im_mov into im_ref.

    Parameters
    ----------
    im_ref : ArrayLike
        Reference image
    im_mov : ArrayLike
        Shifted and rotated image
    upsample_factor : float, optional
        Upsampling determines the accuracy of the underlying shift registration.
        See `phase_cross_correlation` for details, by default 10
    window : Callable, optional
        Window function to apply to the images before determining the frequency magnitude spectrum.
        Needs to take the window length `n` as argument and return a Tensor of shape (n,).
        Default: torch.hann_window

    Returns
    -------
    shift, rot_deg : Tuple[Tuple[float], float]
        Detected shift and rotation that needs to be applied to im_mov to make it
        similar to im_ref.
    """
    im_ref, im_mov = as_tensor(im_ref), as_tensor(im_mov)

    if mode == "shift":
        rot_deg = 0
    elif mode == "rot":
        rot_deg = _register_rot(im_ref, im_mov, upsample_factor, normalization=normalization)
        return (0, 0), rot_deg
    elif mode == "shift_rot":
        # crop quadratic
        min_size = min(min(im.shape) for im in (im_ref, im_mov))
        images = torch.stack([crop_to_shape(im, (min_size, min_size)) for im in (im_ref, im_mov)])

        # register rotation of frequency magnitude spectra
        if window is None:
            window = torch.hann_window
        window_y = window(images.shape[-2]).view(-1, 1)
        window_x = window(images.shape[-1]).view(1, -1)
        spectra = _fft2_center(images * window_x * window_y).abs()
        rot_deg = _register_rot(spectra[0], spectra[1], normalization="phase")

        # rotate moving image
        im_mov = affine_transform2D(im_mov, rotate=rot_deg)
    else:
        raise ValueError(
            f"registration mode {mode} not recognised. Use `shift`, `rot` or `shift_rot`"
        )

    shift = phase_cross_correlation(
        asarray(im_ref),
        asarray(im_mov),
        normalization=normalization,
        upsample_factor=upsample_factor,
    )[0]

    return shift, rot_deg
