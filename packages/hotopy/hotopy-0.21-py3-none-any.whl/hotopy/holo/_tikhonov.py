"""
Reconstruction algorithm in the holographic Fresnel regime.

Author: Jens Lucht
"""

import logging
import numpy as np
import torch
from typing import Callable
from numbers import Number
from torch import as_tensor
from torch.fft import fft2
from torch.linalg import vector_norm as l2norm

from ..optimize import BacktrackingPGM
from ..image import gaussian_bandpass2_real
from . import CTF
from .propagation import FresnelTFPropagator, expand_fresnel_numbers
from .constraints import IdentityOp, ConstraintOperator
from .regularization import twolevel_regularization


logger = logging.getLogger(__name__)


class HomogeneousObject:
    def __init__(self, betadelta=0.0):
        if float(betadelta) == float("+inf"):
            # pure absorption
            self.gamma = 1.0
        else:
            # proportional absorption (also non-absorbing case <=> betadelta == 0)
            self.gamma = 1.0j + betadelta

    def __call__(self, t):
        """
        Homogeneous (complex) refractive object from (real-valued) thickness distribution t.
        """
        return self.gamma * t


class FresnelHologram:
    """
    Simulate hologram by inline holography with Fresnel propagation method.
    """

    def __init__(self, shape, fnums, device=None, dtype=None):
        self.D = FresnelTFPropagator(shape, fnums, device=device, dtype=dtype)
        self.device = device

    def __call__(self, h, p=None):
        """
        Compute holograms

        Parameters
        ----------
        h: array_like
            Complex object function, real part for absorption, imaginary for phase shift.
        p: array_like
            Complex probe/illumination function, real part for absorption, imaginary for phase shift.

        Returns
        -------
        g: array_like
            Intensities at detector.
        """
        h = as_tensor(h, device=self.device)
        u = torch.exp(h)

        if p is not None:
            # with explicit probe function p
            p = as_tensor(p, device=self.device)
            u1 = self.D(p * u)
        else:
            # implicitly assumed plane wave illumination.
            # Here we propagate the _difference_ from the plane wave (constant one).
            u1 = self.D(u - 1) + 1

        # compute intensities
        return torch.square(abs(u1))


class FunctionalOp:
    def __add__(self, other):
        if other is None:
            return self
        return FunctionalSum(self, other)

    def __mul__(self, other):
        if isinstance(other, Number):
            return FunctionalScale(self, other)
        if isinstance(other, FunctionalOp):
            return FunctionalComposition(self, other)
        return NotImplemented

    __rmul__ = __mul__


class FunctionalSum(FunctionalOp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, x):
        return self.left(x) + self.right(x)


class FunctionalComposition(FunctionalOp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, x):
        return self.left(self.right(x))


class FunctionalScale(FunctionalOp):
    def __init__(self, functional, scale):
        self.func = functional
        self.scale = scale

    def __call__(self, x):
        return self.scale * self.func(x)


class DataFidelity(FunctionalOp):
    def __init__(self, F, g):
        self.F = F
        self.g = g

    def __call__(self, x):
        return 0.5 * l2norm(self.F(x) - self.g).square()


class TikhonovFrequencyRegularization(FunctionalOp):
    def __init__(self, w, device=None, dtype=None):
        self.w = as_tensor(w, device=device, dtype=dtype)

    def __call__(self, x):
        X = fft2(x, norm="ortho")
        return 0.5 * l2norm(self.w * X).square()


def _omit_last_at(i):
    index = i * [slice(None)] + [slice(-1)]
    return tuple(index)


def FiniteDiff(x):
    """
    First-order derivative, but zero-padded to input dimension, i.e. last entry per axis of derivative is set to zero.

    Parameters
    ----------
    x: torch.Tensor
        Array (image) to determine first-order forward finite difference.

    Returns
    -------
    diff: torch.Tensor
        First-order finite differences in shape ``(x.ndim, *x.shape)``.

    Note
    ----
    Compatible with torch autograd.
    """
    # XXX: can easily be made array api compatible
    diff = torch.zeros((x.ndim, *x.shape), dtype=x.dtype, device=x.device)
    for i in range(x.ndim):
        diff[i][_omit_last_at(i)] = torch.diff(x, dim=i)
    return diff


class L1smooth:
    def __init__(self, alpha):
        self.alpha_sq = alpha**2

    def __call__(self, x):
        return torch.sqrt(torch.square(x) + self.alpha_sq)


class TVsmooth(FunctionalOp):
    """
    Smoothed variant of total variation (TV) regularization.

    Implements a smoothed anisotropic TV regularization. Here the non-smooth, non-differentiable L1-norm is approximated
    by a smoothed, differentiable (also in zero) function.

    Parameters
    ----------
    alpha: float
        Smoothing/regularization parameter for total variation regularization.

    Returns
    -------
    f: Callable
        Callable regularization operator, apply with ``TV_loss = f(x)`` returns scalar loss from TV.
    """

    def __init__(self, alpha):
        self.l1smooth = L1smooth(alpha)

    def __call__(self, x):
        grad_x = FiniteDiff(x)
        return torch.sum(self.l1smooth(grad_x))


class Tikhonov:
    r"""
    Nonlinear phase retrieval for the near-field holographic regime. Based on Fresnel propagation with Tikhonov regularization.
    Details can be found in [1]_.

    Parameters
    ----------
    shape : tuple
        Dimensions (pixels) of the images to process.
    fresnel_nums : array-like, float
        Fresnel number(s) of the holograms to reconstruct. Scalar for single measurment reconstruction.
        If `(J,)` shaped, J distances are to be reconstructed, astigmatism is support trough shape`(J, 2)`.
    betadelta : float, Optional
        Homogeneous object, also known as single material object, constraint applied to reconstruction.
        I.e. the constraint :math:`\phi = c_{\beta/\delta}\mu` is applied and hence only one unknown (here :math:`\phi`)
        remains.
        Defaults to ``0.0`` i.e. the non-absorbing object.
    alpha : None, float, Tuple[float], Optional
        Tikhonov regularization strength, defaults to ``None`` for no regularization.

        If float, constant Tikhonov regularization will be applied.

        If 2-tuple ``(alpha_lowfreq, alpha_highfreq)``  twolevel regularization is applied with transition at first
        pure-phase CTF maximum between ``alpha_lowfreq`` and ``alpha_highfreq``.
    dtype: torch.dtype, None, Optional
        Datatype to perform calculations with. Commonly used is ``torch.float32`` or ``torch.float64``.

        .. Note:: This datatype preceeds entered data and conversion will be applied if needed.
    device : torch.device, None, Optional
        Compute device to perform reconstruction on. Defaults to `None` (no change of current device). Use `'cuda'` for CUDA based GPU
        computations or integer of GPU-card index, if multiple are present.

    Example
    -------
    Here, we compare the linear (CTF) and nonlinear (Tikhonov) reconstructions for a simulated phantom.

    >>> import numpy as np
    >>> from hotopy.datasets import dicty
    >>> from hotopy.holo import simulate_hologram
    >>> fresnel_nums = [5e-3, 3e-3, 2.33e-3]
    >>> betadelta = 5e-3
    >>> max_phase = 4.0  # rad
    >>> holograms = simulate_hologram(-max_phase*dicty(), fresnel_nums, betadelta=betadelta, npad=1.66)
    >>> rng = np.random.default_rng(seed=1456)
    >>> holograms += rng.normal(0, 0.05, size=holograms.shape)

    GPU reconstruction with homogeneous object assumption and two-level regularization. Note, that with
    ``betadelta > 0`` the regularization of the low frequcies (first alpha entry) can be omitted.

    >>> from hotopy.holo import CTF, Tikhonov, Constraints
    >>> imshape = holograms.shape[-2:]
    >>> ctf = CTF(imshape, fresnel_nums, alpha=(0, 5e-2), betadelta=betadelta, device="cuda")
    >>> tikhonov = Tikhonov(imshape, fresnel_nums, alpha=(0, 5e-2), betadelta=betadelta, device="cuda")

    Now reconstruction using linear CTF and nonlinear Tikhonov

    >>> rec_ctf = ctf(holograms).cpu().numpy()
    >>> rec_nlin = tikhonov(holograms).cpu().numpy()

    With phase non-positivity constraint (:math:`\phi \in \{\phi : \phi \leq 0\quad\mathrm{element-wise}\}`).
    We allow some more iterations for stronger constraints problems.

    >>> constraints = Constraints(phase_max=0)
    >>> rec_ctf_neg = ctf(holograms, constraints=constraints, max_iter=200).cpu().numpy()
    >>> rec_nlin_neg = tikhonov(holograms, constraints=constraints, max_iter=200).cpu().numpy()

    References
    ----------
    .. [1]
        Huhn, S., Lohse, L. M., Lucht, J., & Salditt, T. (2022). Fast algorithms for nonlinear and constrained phase
        retrieval in near-field X-ray holography based on Tikhonov regularization. Optics Express, 30(18), 32871-32886.
        :doi:`10.1364/OE.462368`
    """

    def __init__(
        self, shape, fresnel_nums, betadelta=0.0, alpha=(1e-3, 1e-1), device=None, dtype=None
    ):
        self.shape = tuple(np.atleast_1d(shape))
        self.ndim = len(shape)
        self.device = device
        self.dtype = dtype
        self.betadelta = betadelta
        self.fresnel_nums = expand_fresnel_numbers(fresnel_nums, ndim=self.ndim)

        # forward / direct problem
        self.probe = None  # (complex) probe function. None corresponds to plane wave illumination.
        Fh = FresnelHologram(shape, self.fresnel_nums, device=device, dtype=dtype)
        hom = HomogeneousObject(betadelta)

        def F(x):
            return Fh(hom(x), self.probe)

        self.F = F

        # regularization term (callable or None)
        self.R = None

        if alpha is not None:
            alpha = np.atleast_1d(alpha)
            if len(alpha) == 1 and alpha.ndim == 1:
                w = alpha[0]
            elif len(alpha) == 2 and alpha.ndim == 1:
                w = 2 * np.sqrt(twolevel_regularization(shape, fresnel_nums, alpha=alpha))
            else:
                w = alpha

            self.R = TikhonovFrequencyRegularization(w, device=device, dtype=dtype)

        # initial step size, i.e.
        # the inverse Lipschitz constant (or largest singular value over all frequencies) of the homogeneous CTF, i.e.
        # the linear model, operator. It assumes that all Fresnel numbers are similar and regularization is added in
        # a direct manner.
        if alpha is not None:
            self.tau = 1 / (4 * len(self.fresnel_nums) * (1 + betadelta**2) + np.max(alpha))
        else:
            self.tau = 1 / (4 * len(self.fresnel_nums) * (1 + betadelta**2))

        # setup initial guess from linearized (CTF)
        self.ctf = CTF(
            self.shape, self.fresnel_nums, alpha, betadelta=betadelta, device=device, dtype=dtype
        )

    def __call__(self, holos, constraints=None, x=None, max_iter=100, rtol=3e-3, **solver_opts):
        holos = as_tensor(holos, device=self.device)

        # initial guess
        if x is None:
            if self.probe is None:
                # without probe function i.e. in plane wave case use CTF initialization
                x = self.ctf(holos, constraints=constraints, max_iter=max(max_iter, 30))

                x = nonlinearity_low_freq_correction(
                    x.cpu().numpy(), self.fresnel_nums, self.betadelta
                )
            else:
                # otherwise start with empty reconstruction
                x = torch.zeros(self.shape, dtype=self.dtype, device=self.device)
        x = as_tensor(x, device=self.device, dtype=self.dtype)

        S = DataFidelity(self.F, holos)
        Loss = S + self.R

        if constraints is None:
            proxG = IdentityOp()
        elif isinstance(constraints, Callable):
            proxG = constraints
        else:
            raise ValueError(
                f"{self.__class__.__name__}: Unsupported value for 'constraints' argument. Can be 'None' or any callable function"
                f"with signature 'func(x, t=None)'."
            )
        if isinstance(proxG, ConstraintOperator):
            proxG.to_device(self.device)

        solver_defaults = {
            "tau": self.tau,
            "n_mem": 2,
            "ls_evals": 5,
            "ls_decrease_factor": 4.0,
            "adaptive": True,
            "bb_rule": "alternating",
        }
        solver_opts = {**solver_defaults, **solver_opts}

        pgm = BacktrackingPGM(
            x,
            Loss,
            proxG,
            **solver_opts,
        )

        x_res = pgm(max_iter=max_iter, rtol=rtol)

        return x_res


class TikhonovTV(Tikhonov):
    """
    Nonlinear Fresnel phase retrieval with total variation and Tikhonov-type frequency regularization.
    """

    def __init__(self, *args, alpha_tv=None, **kwargs):
        if alpha_tv is None:
            raise ValueError(f"{self.__class__.__class__}: alpha_tv needs to be passed")

        super().__init__(*args, **kwargs)

        # add smoothed TV regularization chained after Tikhonov-frequency regularization
        self.R = TVsmooth(alpha_tv) + self.R


def nonlinearity_low_freq_correction(img, fresnel_nums, betadelta):
    """
    Preliminary nonlinearity-correction in the reconstructed absorption, applied in the low-frequency regime.
    The idea is the following: the CTF-reconstruction fits the mean value of the phase, phi_0, such
    that 1-(2*betaDeltaRatio)*phi_0 ~ I_0 where I_0 is the mean of the measured intensities. In the
    nonlinear model, however, it must hold that exp(-(2*betaDeltaRatio)*phi_0) ~ I_0. The correction
    below accounts for this difference between CTF- and nonlinear model by adjusting initialGuess
    accordingly (not only its zero Fourier-frequency (= mean value) but the whole low-frequency
    part of the image).
    For strongly absorbing objects, this correction greatly improves convergence of the iterative
    scheme applied below.
    """

    # only apply to non pure-phase objects
    if not betadelta > 0:
        return img

    img = np.asarray(img)
    if img.ndim != 2:
        raise ValueError("Only 2-dim images supported.")

    cutoff_freq = np.mean(1 / np.sqrt(2 * np.pi * np.asarray(fresnel_nums)))
    abs_img = 2 * betadelta * img
    abs_low_pass = gaussian_bandpass2_real(abs_img, cutoff_freq)
    return img + (np.log(1 + abs_low_pass) - abs_low_pass) / (2 * betadelta)
