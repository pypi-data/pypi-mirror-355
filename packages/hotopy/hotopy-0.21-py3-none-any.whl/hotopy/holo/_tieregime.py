"""
TIE-Regime

TODO: dokumentieren

"""

import numpy as np
import torch
from torch import as_tensor
from torch.fft import fft2, ifft2
from tqdm import tqdm
from ..utils import fftfreqn
from .propagation import expand_fresnel_numbers


def _setup_laplace_kernel(shape, sqdx=1):
    """
    Generate Laplace filter kernel for dimensions shape with squared-normalization sqdx
    (analogous to fftfreq normalization dx).
    """

    q = fftfreqn(shape)
    sqdx = np.broadcast_to(sqdx, len(shape))
    return sum([qi**2 / sqdx_i for qi, sqdx_i in zip(q, sqdx, strict=True)])


class FourierTransferFilter:
    device = None
    _kernel = None
    """Filter kernel (in FFT order)"""

    @property
    def kernel(self):
        return self._kernel

    @kernel.setter
    def kernel(self, val):
        self._kernel = as_tensor(val, device=self.device)

    def _apply_filter(self, im):
        return ifft2(fft2(im) * self.kernel).real

    def _reconstruct(self, im):
        raise NotImplementedError

    def __call__(self, im, keep_type=True):
        im_type = type(im)
        im = as_tensor(im, device=self.device)

        rec = self._reconstruct(im)

        if keep_type and im_type is np.ndarray:
            out = rec.cpu().numpy()
        else:
            out = rec
        return out

    def apply_stack(self, stack, chunksize=10):
        stack = as_tensor(stack)  # do not move stack
        target = torch.empty_like(stack, device="cpu")  # target on CPU

        n = len(stack)
        chunksize = int(chunksize)
        nchunks = (n + chunksize - 1) // chunksize  # floor

        for i in tqdm(list(range(nchunks))):
            low = i * chunksize
            high = low + chunksize
            target[low:high] = self(stack[low:high]).cpu()

        return target


class BronnikovAidedCorrection(FourierTransferFilter):
    """
    Create a callable Bronnikov Aided Correction-filter.

    Parameters
    ----------
    imshape : shape-like
        Shape of input holograms.
    alpha : float
        Regularization parameter.
    gamma : float, optional
        Strength of the correction. (Default = 1.0)

    Returns
    -------
    f : BronnikovAidedCorrection
        Callable object ``f(im)`` for applying the BAC-filter on ``im``

    See Also
    --------
    ModifiedBronnikov: The MBA filter.

    Notes
    -----
    See [1]_.

    References
    ----------
    .. [1] Witte, Y. D. et. al., "Bronnikov-aided correction for x-ray computed
           tomography", J. Opt. Soc. Am. A, OSA, 2009, 26, 890-894
    """

    def __init__(self, imshape, alpha, gamma=1.0, device=None):
        if alpha <= 0:
            raise ValueError("alpha must be positive")

        self.gamma = gamma
        self.device = device

        qx, qy = fftfreqn(imshape, 1 / (2 * np.pi))
        laplace_kernel = -(qx**2 + qy**2)

        self.kernel = -laplace_kernel / (-laplace_kernel + alpha)

    def _reconstruct(self, im):
        """
        Apply the BAC-filter on im.

        Parameters
        ----------
        im : ndarray
            Hologram

        Returns
        -------
        out : ndarray
            The BAC-filtered hologram.
        """
        C = -self._apply_filter(im - 1)
        out = -torch.log(im / (1 - self.gamma * C))

        return out


class ModifiedBronnikov(FourierTransferFilter):
    """
    Create a callable Modified Bronnikov-filter.

    Parameters
    ----------
    imshape : shape-like
        Shape of input holograms.
    fresnel_number: float
        Fresnel number.
    alpha : float
        Regularization parameter.

    Returns
    -------
    f : ModifiedBronnikov
        Callable object ``f(im)`` for applying the MBA-filter on ``im``

    See Also
    --------
    BronnikovAidedCorrection: The BAC filter.

    Notes
    -----
    See [1]_.

    References
    ----------
    .. [1] Boone, M. et. al., "Practical use of the modified Bronnikov
           algorithm in micro-CT", Nucl. Instr. and Methods in Phys. Res. Sec.
           B, 2009, 267, 1182-1186
    """

    def __init__(self, imshape, fresnel_numbers, alpha, device=None):
        if alpha <= 0:
            raise ValueError("alpha must be non-negative.")

        self.device = device

        fresnel_numbers = expand_fresnel_numbers(fresnel_numbers, shape=imshape)
        if len(fresnel_numbers) != 1:
            raise ValueError(
                f"Invalid Fresnel numbers given. {self.__class__.__name__} only supports single distance phase"
                f"retrieval. Format for astigmatism is `[[f_y, f_x]]`."
            )

        laplace_kernel = -_setup_laplace_kernel(imshape, fresnel_numbers[0] / (2 * np.pi) ** 2)
        self.kernel = -1 / (-laplace_kernel + alpha / np.mean(fresnel_numbers))
        # NOTE: with astigmatism, the rescaling by the mean Fresnel number is only an approximation.

    def _reconstruct(self, im):
        """
        Apply the MBA-filter on im.

        Parameters
        ----------
        im : ndarray
             Hologram

        Returns
        -------
        out : ndarray
            The MBA-filtered hologram.
        """
        C = self._apply_filter(im - 1)
        out = (-2 * np.pi) * C

        return out


class Paganin(FourierTransferFilter):
    """
    Create a callable Paganin-filter.

    Parameters
    ----------
    imshape : shape-like
        Shape of input hologram.
    fresnel_number: float, array_like
        Fresnel number or list of Fresnel numbers for astigmatism in ``[[f_x, f_y]]`` format.
    betadelta : float
        The beta/delta ratio.

    Returns
    -------
    f : Paganin
        Callable object ``f(im)`` for applying the Paganin-filter on ``im``

    See Also
    --------
    GeneralizedPaganin: The GPM filter.

    Notes
    -----
    See [1]_.

    References
    ----------
    .. [1] Paganin et al.
    """

    def __init__(self, imshape, fresnel_numbers, betadelta, device=None):
        if betadelta <= 0:
            raise ValueError("betadelta (beta-delta-ratio) must be non-negative.")

        fresnel_numbers = expand_fresnel_numbers(fresnel_numbers, shape=imshape)
        if len(fresnel_numbers) != 1:
            raise ValueError(
                f"Invalid Fresnel numbers given. {self.__class__.__name__} only supports single distance phase"
                f"retrieval. Format for astigmatism is `[[f_x, f_y]]`."
            )

        self.device = device
        self.beta_delta_ratio = betadelta

        alpha = 4 * np.pi * betadelta
        laplace_kernel = -_setup_laplace_kernel(imshape, fresnel_numbers[0] / (2 * np.pi) ** 2)
        self.kernel = alpha / (-laplace_kernel + alpha)

    def _reconstruct(self, im):
        """
        Apply the Paganin-filter on im.

        Parameters
        ----------
        im : ndarray
            Hologram

        Returns
        -------
        out : ndarray
            The Paganin-filtered hologram.
        """
        C = self._apply_filter(im)
        out = 1 / (2 * self.beta_delta_ratio) * torch.log(C)

        return out


class GeneralizedPaganin(FourierTransferFilter):
    """
    Create a callable Generalized Paganin-filter.

    Parameters
    ----------
    imshape : shape-like
        Shape of input holograms.
    fresnel_number: float, array_like
        Fresnel number or list of Fresnel numbers for astigmatism in ``[[f_x, f_y]]`` format.
    beta_delta_ratio : float
        The beta/delta ratio.

    Returns
    -------
    f : GeneralizedPaganin
        Callable object ``f(im)`` for applying the GPM-filter on ``im``

    See Also
    --------
    Paganin: The Paganin method.

    Notes
    -----
    See [1]_.

    References
    ----------
    .. [1] Paganin et al.
    """

    def __init__(self, imshape, fresnel_numbers, beta_delta_ratio, device=None):
        if beta_delta_ratio <= 0:
            raise ValueError("beta_delta_ratio must be positive")
        fresnel_numbers = expand_fresnel_numbers(fresnel_numbers, shape=imshape)
        if len(fresnel_numbers) != 1:
            raise ValueError(
                f"Invalid Fresnel numbers given. {self.__class__.__name__} only supports single distance phase"
                f"retrieval. Format for astigmatism is `[[f_x, f_y]]`."
            )

        self.device = device
        self.beta_delta_ratio = beta_delta_ratio

        qx, qy = fftfreqn(imshape, 1 / (2 * np.pi))
        fx, fy = fresnel_numbers[0]
        alpha = 4 * np.pi * beta_delta_ratio
        self.kernel = alpha / (alpha - 2 * ((np.cos(qx) - 1) / fx + (np.cos(qy) - 1) / fy))

    def _reconstruct(self, im):
        """
        Apply the Paganin-filter on im.

        Parameters
        ----------
        im : ndarray
            Hologram

        Returns
        -------
        out : ndarray
            The GPM-filtered hologram.
        """
        C = self._apply_filter(im)
        out = 1 / (2 * self.beta_delta_ratio) * torch.log(C)

        return out
