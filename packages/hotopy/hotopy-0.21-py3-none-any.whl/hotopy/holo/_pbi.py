import numpy as np
import torch
from torch import fft

from .regularization import twolevel_regularization
from .propagation import phase_chirp, expand_fresnel_numbers


class ICT:
    r"""
    Callable `Intensity contrast transfer` (ICT) phase reconstruction.

    Slightly modified reconstruction method based on [1]_.

    The reconstructions is the Tikhonov-regularized least squares solution:

    .. math::
        \phi_* = \frac{\delta}{2\beta}\ln
                \mathcal{F}^{-1} \left[ \left( H^\top H + \alpha \right)^{-1} H^\top \mathcal{F}I \right]

    Parameters
    ----------
    shape: tuple
        Dimension of holograms to reconstruct
    fresnel_num: float, array_like
        Pixel Fresnel numbers or list thereof for multiple distances datasets.
    betadelta: float
        Proportionality factor between absorption and phase shift in complex refractive index. Needs to be strictly
        larger than zero :math:`\frac{\beta}{\delta} > 0`.
    alpha: float, tuple, Optional
        Regularization value. Can either be a single scalar to be constant over all frequencies or 2-tuple
        `(alpha_low, alpha_high)` with different values to low and high frequencies. Defaults to 0, no regularization.
    device: torch.device, Optional
        Device to perform computations on.
    dtype: torch.dtype, Optional
        Datatype to cast kernel into.

    Returns
    -------
    f: Callable
        Callable reconstruction function. Apply to hologram ``y`` with ``f(y)``.

    See also
    --------
    CTF
    Tikhonov
    ModifiedBronnikov

    References
    ----------
    .. [1]
        T. Faragó, R. Spiecker, M. Hurst, M. Zuber, A. Cecilia, and T. Baumbach,
        "Phase retrieval in propagation-based X-ray imaging beyond the limits of transport of intensity and contrast
        transfer function approaches," Opt. Lett.  49, 5159-5162 (2024).
        :doi:`10.1364/OL.530330`
    """

    def __init__(self, shape, fresnel_nums, betadelta, alpha=0.0, device=None, dtype=None):
        self.shape = shape = tuple(np.atleast_1d(shape))
        self.ndim = len(shape)
        self.device = device
        self.dtype = dtype
        self.stack_axis = -self.ndim - 1

        if self.ndim != 2:
            raise NotImplementedError(
                f"{self.__class__.__name__} only implemented for 2-dim images."
            )
        if not betadelta > 0:
            raise ValueError(
                f"{self.__class__.__name__}: {betadelta = :} needs to be strictly larger than zero."
            )

        # modification from paper: we apply twolevel regularization if alpha in ``(alpha_low, alpha_high)`` notation
        if np.size(alpha) == 2:
            alpha = twolevel_regularization(shape, fresnel_nums, alpha)

        self._deltabeta2 = 1.0 / betadelta / 2
        fresnel_nums = expand_fresnel_numbers(fresnel_nums, ndim=self.ndim)
        chi = phase_chirp(shape, fresnel_nums)
        A = np.cos(chi) + 1.0 / betadelta * np.sin(chi)
        AtA = (A**2).sum(self.stack_axis) + alpha

        self.A = torch.asarray(A, device=device, dtype=dtype)
        self.AtA = torch.asarray(AtA, device=device, dtype=dtype)

    def __call__(self, holos):
        y = torch.as_tensor(holos, device=self.device)
        if holos.ndim == self.ndim:
            y = y[np.newaxis]  # add auxiliary axis to reduce later with mean operation
        Y = fft.fft2(y)
        X = (self.A * Y).sum(self.stack_axis) / self.AtA
        x = self._deltabeta2 * torch.log(fft.ifft2(X))
        return x.real
