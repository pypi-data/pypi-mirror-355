"""
Contrast transfer function (CTF) based reconstruction.

.. autosummary::
    :toctree: generated/

    CTF

..
    author: Jens Lucht, 2024
"""

import logging
from typing import Callable
import numpy as np
import torch
from numpy import inf
from torch import real, as_tensor
from torch.fft import fftn, ifftn

from ..optimize import FADMM
from .propagation import phase_chirp, expand_fresnel_numbers
from .regularization import twolevel_regularization

logger = logging.getLogger(__name__)


class CTF:
    r"""
    Contrast transfer function (CTF) based phase retrieval with optional frequency-weighted regularization.
    Supports reconstruction of holograms of multiple distances with and without homogeneous object assumption [1]_
    and reconstruction under object constraints [2]_, such as finite support or non-positivity.

    Mathematically, the Tikhonov-type regularized linear least squares problem is solved,

    .. math:: \min_x \|Ax-y\|^2 + \alpha \|Rx\|^2,

    where :math:`A` is the CTF forward operator, :math:`R` a regularization operator and :math:`y` the measured intensity
    data. The Tikhonov regularized least squares solution is given by,

    .. math:: x^{min} = ( A^T A + \alpha R^T R )^{-1} A^T y.

    The regularization :math:`R` built-in is a Fourier-frequency regularization.

    Parameters
    ----------
    shape : tuple
        Dimensions (pixels) of the images to process.
    fresnel_nums : array-like, float
        Fresnel number(s) of the holograms to reconstruct. Scalar for single measurment reconstruction.
        If `(J,)` shaped, J distances are to be reconstructed, astigmatism is support trough shape`(J, 2)`.
    alpha : None, float, Tuple[float], Optional
        Tikhonov regularization strength, defaults to ``None`` for no regularization.

        If float, constant Tikhonov regularization will be applied to diagonal.

        If 2-tuple ``(alpha_lowfreq, alpha_highfreq)``  or (2, 2)-tuple (in same notation for for phase and absorption)
        in non-homogeneous case twolevel regularization is applied, with transition at first pure-phase CTF maximum
        between ``alpha_lowfreq`` and ``alpha_highfreq``.

        .. note::
            Any Tikhonov-type regularization can be manually applied onto :math:`A^\top A` by

            >>> ctf = CTF(shape, fresnel_nums)
            >>> ctf.AtA += RtR  # where RtR is the regularization

            ``RtR`` can be scalar or a function of ``fftfreqn(shape)``.
    betadelta : float, None, Optional
        If not numeric value, apply homogeneous object, also known as single material object, constraint to reconstruction.
        The passed value is used as proportionallity between phase and absorption, i.e.
        :math:`\phi = c_{\beta/\delta}\mu` is used within the forward model and hence only (here :math:`\phi`)
        remains as unknown.

        If ``None`` both phase and absorption will be reconstructed (non-homogeneous/generic CTF). By default,
        no coupling between phase and absorption is enforced.
    npad: int, Tuple[int] None, Optional
        Factor to zero (!) pad holograms with. Padding (or if npad < 1 cropping) can be set per dimension, e.g. with
        ``npad = (1.5, 1)`` and 2-dimensional image will be padded only in the first (height) axis.
    dtype: torch.dtype, None, Optional
        Datatype to perform calculations with. Commonly used is ``torch.float32`` or ``torch.float64``.

        .. Note:: This datatype preceeds entered data and conversion will be applied if needed.
    device : torch.device, None, Optional
        Compute device to perform reconstruction on. Defaults to `None` which is `'cpu`'. Use `'cuda'` for CUDA based GPU
        computations or integer of GPU-card index, if multiple are present.

    Example
    -------
    GPU reconstruction with homogeneous object assumption and two-level regularization. Note, that with
    ``betadelta > 0`` the regularization of the low frequcies (first alpha entry) can be omitted.

    >>> from hotopy.holo import CTF, Constraints
    >>> imshape = holograms.shape[-2:]
    >>> ctf = CTF(imshape, fresnel_nums, alpha=[0, 5e-2], betadelta=1e-3, device="cuda")
    >>> rec_phase = ctf(holograms).cpu().numpy()  # gather reconstruction from GPU to CPU and wrap as NumPy ndarray.

    With phase non-positivity constraint (:math:`\phi \in \{\phi : \phi \leq 0\quad\mathrm{element-wise}\}`)

    >>> constraints = Constraints(phase_max=0)
    >>> rec_neg_phase = ctf(holograms, constraints=constraints).cpu().numpy()

    References
    ----------
    .. [2]
        Huhn, S., Lohse, L. M., Lucht, J., & Salditt, T. (2022). Fast algorithms for nonlinear and constrained phase
        retrieval in near-field X-ray holography based on Tikhonov regularization. Optics Express, 30(18), 32871-32886.
        :doi:`10.1364/OE.462368`
    .. [3]
        Lucht, J., Lohse, L. M., Hohage, T., & Salditt, T. (2024). Phase retrieval beyond the homogeneous object
        assumption for X-ray in-line holographic imaging. arXiv preprint :arXiv:`2403.00461`.

    """

    @property
    def At(self):
        return self.A.swapaxes(-2, -1)

    def __init__(
        self,
        shape,
        fresnel_nums,
        alpha=None,
        betadelta=0.0,
        npad=1,
        device=None,
        dtype: torch.dtype = None,
    ):
        self.device = device
        self.betadelta = betadelta
        self.alpha = alpha
        self.shape = shape = tuple(shape)
        self.ndim = len(shape)
        self.fft_shape = tuple(np.multiply(shape, npad or 1).astype(int))
        # precompute slice to crop padding on final result
        self.slice_to_shape = (
            ...,  # do no touch leading axes
            *[slice(si) for si in shape],  # crop in images dimensions
            slice(None),  # no cropping in Q axis
        )

        fresnel_nums = expand_fresnel_numbers(fresnel_nums, ndim=self.ndim)
        chi = phase_chirp(self.fft_shape, fresnel_nums, ndim=self.ndim)
        chi = np.moveaxis(chi, -self.ndim - 1, -1)  # move J axis to last

        # compute forward kernel in (..., *shape, J, Q) shape
        s, c = 2 * np.sin(chi), 2 * np.cos(chi)
        if betadelta is not None:
            if betadelta == 0:
                # pure phase object (beta == 0)
                A = s
            elif betadelta == inf:
                # pure absorption (delta == 0)
                A = c
            else:
                # homogeneity of absorption and phase approximation
                A = s + betadelta * c

            # expand with Q = 1 in last axis
            A = A[..., np.newaxis]
        else:
            # generic (inhomogeneous) case
            # Q = 2 in last axis
            A = np.stack([s, c], axis=-1)

        self.J, self.Q = A.shape[-2:]

        # covariance (aka AtA) operator
        AtA = A.swapaxes(-2, -1) @ A

        # add regularization, if given
        if alpha is not None:
            # scalar behaves identical in all cases:
            if np.isscalar(alpha):
                # NOTE: for consistency with HoloTomoToolbox (MATLAB) multiplication by 2 is required
                AtA += 2 * alpha * np.eye(self.Q)

            # check for homogeneous case, apply two-level regularization
            elif betadelta is not None:
                if len(alpha) == 2:
                    # NOTE: for consistency with HoloTomoToolbox (MATLAB) multiplication by 2 is required
                    AtA[..., 0, 0] += 2 * twolevel_regularization(
                        self.fft_shape, fresnel_nums, alpha
                    )
                else:
                    raise ValueError(
                        f"{self.__class__.__name__}: Invalid regularization parameter alpha given."
                    )

            # check for two-level regularization in non-homogeneous case
            else:
                alpha = np.asarray(alpha)
                # two-level regularization in phase and absorption independently
                if alpha.shape == (2, 2):
                    for qi in range(2):
                        AtA[..., qi, qi] += 2 * twolevel_regularization(
                            self.fft_shape, fresnel_nums, alpha[qi]
                        )
                else:
                    raise ValueError(
                        f"{self.__class__.__name__}: Invalid regularization parameter alpha given."
                    )

        self.A = as_tensor(A, device=self.device, dtype=dtype)
        self.AtA = as_tensor(AtA, device=self.device, dtype=dtype)
        self.dtype = self.A.dtype

    def At_mul(self, b):
        """
        Computes adjoined operator A applied on b.

        Parameters
        ----------
        b: tensor
            Data vector in ``(..., *shape, J)`` shape

        Returns
        -------
        tensor:
            Adjoined in ``(..., *shape, Q)``
        """
        return (self.A * b[..., np.newaxis]).sum(-2)

    def prox(self, b) -> "ProxCTF":
        """
        Setup proximal CTF inversion operator from measurement data b.

        Parameters
        ----------
        b: array-like, tensor
            Measurement data (intensity data) in ``(..., J, *shape)``
        """
        b = as_tensor(b, device=self.device, dtype=self.dtype)
        B = fftn(
            b - 1, s=self.fft_shape
        )  # FFT over last ndim axes, potentially applying zero padding
        B = torch.moveaxis(B, -self.ndim - 1, -1)

        Atb = self.At_mul(B)

        return ProxCTF(self.fft_shape, self.AtA, Atb)

    def constrained(self, b, constraints, **kwargs) -> "ConstrainedCTF":
        # setup different constrained CTF options for homogeneous and non-homogeneous case
        if self.betadelta is None:
            defaults = {
                "tau": 1e-2,
            }
        else:
            defaults = {
                "tau": 5e-4,
            }

        shape = (*self.fft_shape, self.Q)
        kwargs = {**defaults, **kwargs}

        return ConstrainedCTF(
            shape, self.prox(b), constraints, device=self.device, dtype=self.dtype, **kwargs
        )

    def __call__(self, holograms, constraints=None, unpack=True, **kwargs):
        """
        Reconstruct given hologram(s).

        Parameters
        ----------
        holograms: array-like, tensor-like
            Single or stack of holograms to reconstruct from. Stack is expected in first axis, e.g. a four hologram
            stack should have shape ``(4, *self.shape)``.
        constraints: None, Constraints, Callable, Optional
            Constraints to enforce onto the reconstruction.
        unpack: bool, Optional
            If homogeneous object assumption is applied, remove additional stack axis, which is done by default.
        kwargs: Optional
            Arguments to pass to the ConstrainedCTF initialization.

        Returns
        -------
        tensor:
            Phase reconstruction if ``betadelta != None``, otherwise stack of phase and absorption (in this order)
            reconstructions.
        """
        holograms = as_tensor(holograms, device=self.device, dtype=self.dtype)

        if holograms.ndim < self.ndim:
            raise ValueError(
                f"{self.__class__.__name__}: Holograms do not match dimensions given to initialization."
            )
        if holograms.ndim == self.ndim:
            # expand single hologram to stack of one hologram (J = 1)
            holograms = holograms[np.newaxis]
        j_holos = holograms.shape[-self.ndim - 1]
        if j_holos != self.J:
            raise ValueError(
                f"{self.__class__.__name__}: Number of given holograms ({j_holos}) does not match number of Fresnel "
                f"numbers at initialization ({self.J})."
            )

        # without constraints: direct Tikhonov-regularized least squares solution. This is the special case of a prox
        # without 'proximity vector' y.
        if constraints is None:
            rec = self.prox(holograms)()

        # with constraints setup ADMM iteration between constraints and proximal CTF and return result
        else:
            rec = self.constrained(holograms, constraints=constraints, **kwargs)()

        # crop to original shape
        out = rec[self.slice_to_shape]

        # unpack single variable if only one
        if unpack and self.Q == 1:
            return out[..., 0]

        # otherwise return in ``(..., Q, *shape)``.
        return torch.moveaxis(out, -1, -self.ndim - 1)


class ProxCTF:
    r"""
    This class computed the proximal least squares solution for the given Atb and AtA operators in Fourier space,
     i.e. it computes:

    .. math:: \mathcal{F}x_{rec} = (A^\top A + t)^{-1} (A^\top b + t \cdot \mathcal{F}y)

    where t is the proximal step size and y (in real space) proximity point.
    """

    def __init__(self, shape, AtA, Atb, device=None):
        self.AtA = as_tensor(AtA, device=device)
        self.Atb = as_tensor(Atb, device=device)
        self.shape = shape
        ndim = len(shape)
        self.fft_dims = tuple(range(-ndim - 1, -1))

    def fftn(self, x):
        return fftn(x, dim=self.fft_dims)

    def ifftn(self, x):
        return ifftn(x, dim=self.fft_dims)

    def __call__(self, y=None, t=0.0):
        """

        y: tensor, None
            Proximity (reconstruction) vector in ``(..., *shape, Q)`` shape or ``None`` for non-proximal least squares
            solution.
        """
        if y is None or t == 0:
            # non-proximal mapping if called without x or zero t
            proxAtb = self.Atb
            proxC = self.AtA
        else:
            proxAtb = self.Atb + t * self.fftn(y)
            proxC = self.AtA + t

        # computed proximal least squares solution
        if self.AtA.shape[-1] == 1:  # recall AtA is square matrix in (..., Q, Q)
            # for speed up, we use trivial inversion in case of Q=1 (homogeneous case)
            Cinv = 1 / proxC[..., 0, 0]
            Xrec = (Cinv * proxAtb[..., 0])[..., np.newaxis]
        else:
            # in case Q > 1, slower matrix inverse (in last 2 axes) is used
            Cinv = torch.linalg.inv(proxC) + 0j
            Xrec = (Cinv @ proxAtb[..., np.newaxis])[..., 0]

        return real(self.ifftn(Xrec))


class ConstrainedCTF(FADMM):
    @property
    def proxG(self):
        return self.proxs[0][0]

    @proxG.setter
    def proxG(self, proxG):
        self.proxs = [(proxG, self.proxH)]

    @property
    def proxH(self):
        return self.proxs[0][1]

    @proxH.setter
    def proxH(self, proxH):
        self.proxs = [(self.proxG, proxH)]

    @property
    def u(self):
        return self.state["u"]

    @property
    def v(self):
        return self.state["v_old"]

    @property
    def niter(self):
        return self.state["niter"]

    def __init__(
        self,
        shape,
        prox_ctf,
        prox_constraints,
        tau=1e-2,
        max_iter=100,
        tolerance=1e-3,
        lmbd=None,
        eta=0.999,
        device=None,
        dtype=None,
        verbose=False,
    ):
        """

        Parameters
        ----------
        shape: tuple
            Shape of images in ``(*shape, Q)``.

        Note
        ----
        Different default ``tau`` due to different scaling of GenericCTF operator.
        """
        # setup reco ...
        self.x = torch.zeros(shape, dtype=dtype, device=device)
        self.max_iter = int(max_iter)
        self.tolerance = tolerance
        self._n_axes = len(shape)

        if lmbd is None:
            lmbd = torch.zeros_like(self.x)

        if hasattr(prox_constraints, "to_device") and isinstance(
            prox_constraints.to_device, Callable
        ):
            prox_constraints.to_device(device)

        # initialize ADMM
        super().__init__(
            [self.x], [(prox_constraints, prox_ctf)], lmbd, eta=eta, stepsize=tau, verbose=verbose
        )

    def __call__(self):
        while self.niter < self.max_iter:
            residuals = self.step()
            k = self.niter

            logger.info(f"CTF-ADMM step {k}: prim={residuals[0]:.2e}, dual={residuals[1]:.2e}")

            if max(residuals) <= self.tolerance:
                logger.info(f"CTF-ADMM converged after {k} steps (tol <= {self.tolerance:.2e})!")
                break
        else:
            logger.info("CTF-ADMM tolerance not reached")

        return self.u
