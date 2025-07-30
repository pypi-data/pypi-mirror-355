"""
=============================================
Optimization methods (:mod:`hotopy.optimize`)
=============================================

.. autosummary::
    :toctree: generated/

    FADMM
    BacktrackingPGM
    FISTA
    AlternatingProjections


..
    author: Jens Lucht, 2021-2024
"""

import logging
import math
from typing import List, Callable

import torch
from torch import as_tensor
from torch.linalg import vector_norm, vector_norm as l2norm


logger = logging.getLogger(__name__)


class Algorithm:
    """Algorithm structure.

    An algorithm should be used like:
    >>> alg = Algorithm()
    >>> while not alg.done():
    ...     alg.step()  # calls algorithm specific .update method.
    """

    state: dict = None
    """Current state of algorithm."""

    monitor: "Monitor" = None

    @property
    def do_monitoring(self) -> bool:
        return self.monitor is not None

    def __init__(self):
        """Initialize algorithm. Set variables, parameters, stepsizes, etc."""
        self.state = {
            "niter": 0,
        }

    def step(self):
        """Perform one step."""
        values = self.update()
        self._monitoring(values)
        self.state["niter"] += 1
        return values

    def done(self) -> bool:
        """Checks convergence and stopping conditions."""

    def update(self):
        """Update of variables (inner step method, .step() shall be called)."""
        raise NotImplementedError

    def _monitoring(self, values):
        if self.do_monitoring:
            self.monitor.step(self, values)


class BacktrackingPGM:
    """
    Proximal gradient method (or projected gradient) with non-monotone backtracking.
    """

    @torch.no_grad()
    def __init__(
        self,
        x,
        F,
        proxG,
        tau=None,
        adaptive=True,
        bb_rule="alternating",
        n_mem=None,
        ls_evals=4,
        ls_decrease_factor=2.0,
        device=None,
    ):
        """
        Parameters
        ---------
        x: tensor
            Target variable
        F:
            smooth function
        proxG:
            proximal mapping of G
        tau: float
            (Initial) step size
        adaptive: bool
            Use adaptive step size. Defaults to True.
        bb_rule: "alternating", "adaptive"
            Which Barzilai-Borwein step size rule to use.
        n_mem: None, int
            size of backtracking memory. Backtracking is disabled if n_mem = 1 (or None).
        """
        tau = float(tau)
        ls_evals = int(ls_evals)
        n_mem = int(n_mem or 1)

        if ls_evals < 1:
            raise ValueError(f"{self.__class__.__name__}: ls_evals need to be strictly > 0.")
        if tau <= 0:
            raise ValueError(
                f"{self.__class__.__name__}: Step size tau needs to be strictly positive."
            )

        self.niter = 0
        self.feval = 0
        self.device = device
        self.F = F
        self.proxG = proxG
        self.x = as_tensor(x, device=device)
        self.x.requires_grad_(True)
        self.x.grad = None
        self.x_hat = None
        self.value = None
        self.tau = None  # step size for current step
        self.tau_new = tau  # step size for next step
        self.adaptive = bool(adaptive)
        self.bb_rule = str(bb_rule or "alternating").lower()
        self.ls_evals = int(ls_evals)
        self.ls_decrease_factor = ls_decrease_factor

        with torch.enable_grad():
            value = self.value = F(self.x)
            value.backward()

        # setup stopping condition based on relative residual
        self.ref_grad = vector_norm(self.x.grad)

        # setup backtracking
        self.memory = torch.full((n_mem,), -torch.inf)
        self.push_memory(value)

    @property
    def residuum(self):
        return compute_residuum(self.x.grad, self.x, self.x_hat, self.tau)

    @property
    def relative_residuum(self):
        return vector_norm(self.residuum) / self.ref_grad

    @torch.no_grad()  # do not accumulate gradients unless explicitly activated
    def step(self):
        """Single update step function"""
        self.niter += 1
        tau = float(self.tau_new)

        f_max = torch.max(self.memory)

        for n_eval in range(self.ls_evals):
            # forward step: gradient decent step
            self.x_hat = self.x - tau * self.x.grad

            # backward step: proximal (projection) step
            x_new = self.proxG(self.x_hat, tau)

            # compute backtracking line search condition
            delta_x = x_new - self.x
            value_decrease_cond = (
                f_max
                + (delta_x.conj() * self.x.grad).real.sum()
                + (0.5 / tau) * delta_x.abs().square().sum()
            )
            self.tau = tau  # save tau which is actually used

            # evaluate error/loss functional
            # here gradient accumulation needs to be enabled in forward pass
            with torch.enable_grad():
                self.feval += 1
                x_new.requires_grad_(True)
                value_new = self.F(x_new)

            if value_new < value_decrease_cond:
                break

            tau /= self.ls_decrease_factor  # reduce step size for next try
        else:
            # no convergence (break statement) within line search
            logger.info(
                f"{self.__class__.__name__}: backtracking line search did not converge within {self.ls_evals}"
                f"evaluations. Continuing anyway."
            )

        value_new.backward()

        # compute next step size
        if self.adaptive:
            # delta_x already computed within line search
            delta_grad = x_new.grad - self.x.grad
            ts, tm = compute_barzilai_borwein(delta_x, delta_grad)

            if self.bb_rule == "alternating":
                if self.niter % 2:
                    tau_new = tm()
                else:
                    tau_new = ts()
            elif self.bb_rule == "adaptive":
                ts = ts()
                tm = tm()
                if tm / ts > 0.5:
                    tau_new = tm
                else:
                    tau_new = ts - 0.5 * tm
            else:
                raise ValueError("unknown bb_rule.")

            # only accept new step size if positive, otherwise keep current step size
            if tau_new > 0:
                self.tau_new = tau_new

        self.push_memory(value_new)
        self.x = x_new
        self.value = value_new

        return x_new, value_new

    @torch.no_grad()
    def __call__(self, max_iter=100, rtol=None):
        """
        Iterate until convergence.


        Parameters
        ----------
        max_iter: int, optional
            Maximal number of iterations per call (!).
        rtol: float, None, optional
            (Normalized) residual tolerance (rtol).
        """
        resi = float("inf")
        done = False
        done_log = None
        for k in range(max_iter):
            x, val = self.step()
            resi = compute_residuum(x.grad, x, self.x_hat, self.tau)

            it_log = f"{self.__class__.__name__}: iteration {self.niter:4d}: loss = {val:.4e} tau = {self.tau:.4e}"

            # check normalized residuum stopping condition
            if rtol is not None:
                resi_rel = vector_norm(resi) / self.ref_grad

                it_log += f" normalized resi = {resi_rel:.4e}"

                if resi_rel <= rtol:
                    done_log = f"{self.__class__.__name__}: FINISHED by RTOL criterion after {self.niter} steps {self.feval} func-evals. rtol = {resi_rel:.4e} <= {rtol:.4e}; |resi| = {vector_norm(resi):.4e}"
                    done = True

            logger.info(it_log)

            if done:
                logger.info(done_log)
                break
        else:
            logger.info(
                f"{self.__class__.__name__}: STOPPED by MAX_ITER criterion after {self.niter} steps {self.feval} func-evals. |resi| = {vector_norm(resi):.4e}"
            )

        return self.x.detach()

    def push_memory(self, val):
        self.memory[self.niter % len(self.memory)] = val


class FISTA:
    def __init__(self, x, F, proxG, tau=None, device=None, dtype=None):
        tau = float(tau)
        if tau <= 0:
            raise ValueError(
                f"{self.__class__.__name__}: Step size tau needs to be strictly positive."
            )

        self.niter = 0
        self.feval = 0
        self.F = F
        self.proxG = proxG
        self.x = as_tensor(x, device=device, dtype=dtype)
        self.y = self.x.clone().detach()
        self.x.requires_grad_(False)
        self.x.grad = None
        self.y.requires_grad_(True)
        self.y.grad = None
        self.y_hat = None  # auxiliary var, after gradient step of F
        self.value = None
        self.tau = tau  # step size, inverse Lipschitz constant
        self.t = 1.0  # Nesterov-like factor
        self.device = self.x.device
        self.dtype = self.x.dtype

        # evaluate error/loss functional
        # here gradient accumulation needs to be enabled in forward pass
        with torch.enable_grad():
            self.feval += 1
            self.value = self.F(self.y)
            self.value.backward()

        # setup stopping condition based on relative residual
        self.ref_grad = vector_norm(self.y.grad)

    @torch.no_grad()
    def step(self):
        self.niter += 1

        # forward step: gradient decent step (note: gradients in y!)
        self.y_hat = self.y - self.tau * self.y.grad

        # backward step: proximal (projection) step
        x_new = self.proxG(self.y_hat, self.tau)

        # Nesterov-like factor
        t_new = (1 + math.sqrt(1 + 4 * self.t * self.t)) / 2

        alpha_t = (self.t - 1) / t_new
        y_new = x_new - alpha_t * (x_new - self.x)

        # evaluate error/loss functional
        # here gradient accumulation needs to be enabled in forward pass
        with torch.enable_grad():
            self.feval += 1
            y_new.requires_grad_(True)
            value_new = self.F(y_new)
            value_new.backward()

        self.x = x_new
        self.y = y_new
        self.value = value_new
        self.t = t_new

        return x_new, value_new

    @torch.no_grad()
    def __call__(self, max_iter=100, rtol=None):
        resi = float("inf")
        done = False
        done_log = None
        for k in range(max_iter):
            x, val = self.step()
            y = self.y
            resi = compute_residuum(y.grad, y, self.y_hat, self.tau)

            it_log = f"{self.__class__.__name__}: iteration {self.niter:4d}: loss = {val:.4e} tau = {self.tau:.4e} t = {self.t:.4e}"

            # check normalized residuum stopping condition
            if rtol is not None:
                resi_rel = vector_norm(resi) / self.ref_grad

                it_log += f" normalized resi = {resi_rel:.4e}"

                if resi_rel <= rtol:
                    done_log = f"{self.__class__.__name__}: FINISHED by RTOL criterion after {self.niter} steps {self.feval} func-evals. rtol = {resi_rel:.4e} <= {rtol:.4e}; |resi| = {vector_norm(resi):.4e}"
                    done = True

            logger.info(it_log)

            if done:
                logger.info(done_log)
                break
        else:
            logger.info(
                f"{self.__class__.__name__}: STOPPED by MAX_ITER criterion after {self.niter} steps {self.feval} func-evals. |resi| = {vector_norm(resi):.4e}"
            )

        return self.x.detach()


class FADMM(Algorithm):
    """
    Fast Alternating Direction Method of Multipliers (fADMM) algorithm for solving of convex optimization problems.

    Implements the alternating direction method of multipliers (ADMM) with Nesterov-type acceleration and restarts.
    For algorithmic details see [2]_, esp. Algorithm 8

    Further reading:
    - J. Eckstein (1992): On the Douglas-Rachford splitting method and proximal point algorithm for maximal monotone operators
    - A. Chambolle, T. Pock (2011), J Math Imaging Vis: A First-Order Primal-Dual Algorithm for Convex Problems
    with Applications to Imaging. DOI 10.1007/s10851-010-0251-1

    Notes
    -----
        This variant uses A=-I, B=I, b=0 and hence is a single parametric solver (as u=v), but with H,G splitting.

    References
    ----------
    .. [2]  Fast Alternating Direction Optimization Methods. T. Goldstein, et al. SIAM J. IMAGING SCIENCES (2014)
            https://doi.org/10.1137/120896219
    """

    @torch.no_grad()
    def __init__(
        self,
        params: list,
        proxs: List[tuple],
        l0,
        stepsize: float = None,
        eta: float = 0.999,
        verbose: bool = False,
    ):
        """
        TODO

        Parameters
        ----------
        params: list
            Parameters (or variables) to optimize
        proxs: list[tuple] = [(proxH, proxG)]
            Proximal operators of functionals as 2-tuple per parameter.
        l0:
            Initial value for lambda.
        stepsize: float
            stepsize/learning rate.
        eta: float, (0, 1)
            restart tuning parameter. Should be close to one, to have infrequent "restarts".
        verbose: bool
            Print status messages
        """
        params = list(params)
        proxs = list(proxs)

        # we only support single parameter models
        if len(params) != 1:
            raise ValueError(
                f"{__class__}: more than 1 parameter given in model, which is not supported."
            )

        try:
            [(proxH, proxG)] = proxs
        except (ValueError, KeyError) as e:
            raise ValueError(
                f"{self.__class__.__name__}: two proximal operators for H and G need to be given!"
            ) from e

        # verify eta
        if eta <= 0 or eta >= 1:
            raise ValueError(f"{self.__class__.__name__}: eta needs be between 0 and 1. ")

        super().__init__()

        self.params = params
        self.proxs = proxs
        self.verbose = verbose

        if verbose:
            logger.setLevel(logging.INFO)

        # initialize state
        state = self.state
        param = params[0]

        # set initial values
        self.stepsize = stepsize
        self.eta = eta
        state["lamb_hat"] = l0
        state["alpha"] = 1.0
        state["lamb_old"] = l0
        state["v_old"] = param.data

        # non required value, but used for intermediate value access
        state["u"] = None
        state["c"]: float = None

    @torch.no_grad()
    def update(self):
        """Perform one ADMM update step.

        Note: Updates parameter(s) inplace. Use ImplicitFunctional to wrap any explicit functional.

        Returns
        -------
        float, float:
            Primal and dual residual
        """

        [param] = self.params
        [(proxH, proxG)] = self.proxs
        stepsize = self.stepsize
        eta = self.eta
        state = self.state

        lamb_hat = state["lamb_hat"]  # lambda hat
        lamb_old = state["lamb_old"]  # lambda k-1
        v_old = state["v_old"]  # v(k-1)
        alpha = state["alpha"]  # alpha
        v_hat = param.data  # v hat

        # proximal step (in H and G)
        u = proxH(v_hat - lamb_hat, t=stepsize)
        v = proxG(u + lamb_hat, t=stepsize)

        # update lambda and residuals
        lamb = lamb_hat + (u - v)
        resi_primal = l2norm(u - v)
        resi_dual = l2norm(v - v_hat)
        c = stepsize * (resi_primal**2 + resi_dual**2)

        # check convergence
        # NOTE: c is current iterate (k), state["c"] of previous (k-1)
        if state["niter"] == 0 or c < eta * state["c"]:
            # case 1: converging
            logger.debug(f"{self.__class__.__name__}: case 1 - converging")
            alpha_new = (1.0 + (1.0 + 4 * alpha**2) ** 0.5) / 2
            nesterov = (alpha - 1) / alpha_new
            state["alpha"] = alpha_new
            state["lamb_old"] = lamb
            state["lamb_hat"] = lamb.add(lamb - lamb_old, alpha=nesterov)
            state["c"] = c
            state["v_old"] = v

            # (inplace) update variable
            param.data = v + nesterov * (v - v_old)
        else:
            # case 2: "restart"
            logger.debug(f"{self.__class__.__name__} case 2 - RESTART")
            state["alpha"] = 1.0
            state["c"] /= eta
            state["lamb_hat"] = lamb_old

            # (inplace) update variable
            param.data = v_old

        state["u"] = u

        # relative residuals
        norm_v, norm_u, norm_v_hat = l2norm(v), l2norm(u), l2norm(v_hat)
        resi_primal /= torch.max(norm_u, norm_v)
        resi_dual /= torch.max(norm_v_hat, norm_v)

        return resi_primal, resi_dual


class AlternatingProjections(Algorithm):
    def __init__(self, forward, projs, x, max_iter: int = 100):
        projs = tuple(projs)

        if len(projs) != 2:
            raise ValueError(f"{self.__class__.__name__} Need 2 projectors")

        super().__init__()

        self.forward = forward
        self.proj_0, self.proj_1 = projs
        self.x = x
        self.max_iter = int(max_iter)

    def update(self):
        # propagator to detector
        u1 = self.state["u1"] = self.forward(self.x)

        # project amplitudes in detector
        u1new = self.proj_1(u1)

        # propagator back to sample
        u0new = self.forward.inverse(u1new).mean(0)

        # apply object constrains
        self.x = self.proj_0(u0new)

    def done(self):
        return self.state["niter"] >= self.max_iter


def get_stepsize_method(name_or_method) -> Callable:
    if isinstance(name_or_method, Callable):
        return name_or_method
    elif name_or_method in ["barlizai_borwein", "adaptive"]:
        return stepsize_barlizai_borwein
    elif name_or_method == "constant":
        return stepsize_constant
    else:
        raise ValueError(f"Unknown stepsize method '{str(name_or_method)}' method.")


@torch.no_grad()
def stepsize_barlizai_borwein(stepsize, param, state):
    """Barlizai-Borwein adaptive step sizes.

    In alternating manner.

    .. note::
        Uses single parameter only for now.

    .. warning::
        Not implemented for complex parameters.

    """
    if state["niter"] == 0:
        return stepsize

    dp = param - state["value"]
    ds = param.grad - state["grad"]

    # TODO: implementation for complex parameters
    if state["niter"] % 2:
        new_stepsize = ds.conj().mul(dp).sum() / ds.square().sum()
    else:
        new_stepsize = dp.square().sum() / dp.conj().mul(ds).sum()

    # ensure non-negativity
    if new_stepsize < 0:
        return stepsize
    return new_stepsize


@torch.no_grad()
def compute_barzilai_borwein(delta_x, delta_grad):
    # Compute scalar products of delta_x, delta_grad combinations. NOTE lazy evaluations for dx_dx dgrad_dgrad
    def dx_dx():
        return (delta_x * delta_x).real.sum()

    def dgrad_dgrad():
        return (delta_grad * delta_grad).real.sum()

    dx_dgrad = (delta_x * delta_grad).real.sum()

    def ts():
        return dx_dx() / dx_dgrad

    def tm():
        return dx_dgrad / dgrad_dgrad()

    return ts, tm


def stepsize_constant(stepsize, param, state):
    return stepsize


def compute_residuum(f_grad, x, x_hat, tau):
    return f_grad + (x_hat - x) / tau


class Monitor:
    def step(self, alg, values):
        """Monitoring step of algorithm alg."""
