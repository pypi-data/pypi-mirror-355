"""
Constraints Opterator
=====================

These operators are to be used in constrained, iterative algorithms. For GPU support these operators are currently
setup up with Torch methods.


.. author: Jens Lucht
"""

from functools import reduce
from typing import Callable, Union
from torch import Tensor, as_tensor, angle, exp, clip
from numpy import ndarray


class ConstraintOperator:
    other = None

    def to_device(self, device):
        for k, v in self.__dict__.items():
            if isinstance(v, ndarray) or isinstance(v, Tensor):
                self.__dict__[k] = as_tensor(v, device=device)

    def __mul__(self, other):
        r"""
        Composition of two operators,  i.e.

            .. math: A(B(x)) = (A * B)(x)

        Returns
        -------
        op: ConstraintOperator
            Composition of both operators.
        """
        if isinstance(other, Callable):
            return OperatorComposition(self, other)
        raise ValueError(
            f"Composition with {__class__.__name__} and '{other.__class__.__name__}' not supported."
        )


class OperatorComposition(ConstraintOperator):
    def __init__(self, left, right):
        self._left = left
        self._right = right

    def __call__(self, x, t=None):
        return self._left(self._right(x, t=t), t=t)

    def to_device(self, device):
        if isinstance(self._left, ConstraintOperator):
            self._left.to_device(device)
        if isinstance(self._right, ConstraintOperator):
            self._right.to_device(device)


class MaskedOperator(ConstraintOperator):
    """Restricted operator that only acts on the data contained in the mask."""

    def __init__(self, mask, operator):
        self.mask = as_tensor(mask).bool()
        self.op = operator

    def __call__(self, u: Tensor):
        return self.op(u) * self.mask + u * ~self.mask

    def to_device(self, device):
        self.mask = self.mask.to(device)
        self.op.to_device(device)


class SupportOp(ConstraintOperator):
    def __init__(self, mask: Union[ndarray, Tensor]):
        self.mask = as_tensor(mask)

    def __call__(self, x, t=None):
        # check if x is vector of images (in last axes, as in CTF) and expand mask accordingly to ensure broadcasting
        # in image axes.
        if x.ndim > 2 and x.shape[-1] <= 2:
            mask = self.mask[..., None]
        else:
            mask = self.mask

        return mask * x


class BoundOp(ConstraintOperator):
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __call__(self, x, t=None):
        return clip(x, self.min, self.max)


class IdentityOp(ConstraintOperator):
    def __call__(self, x, t=None):
        return x


class AmplitudeProjector(ConstraintOperator):
    """
    (Complex) wave function projection onto given amplitudes. E.g. use as magnitude constraint for measured data.
    """

    def __init__(self, amplitude):
        self.amplitude = as_tensor(amplitude)

    def __call__(self, u, t=0.0):
        phase = angle(u)
        return self.amplitude * exp(1j * phase)


class BinnedAmplitudeProjector(AmplitudeProjector):
    """
    (Complex) wave function projection: Projects pixel blocks onto given block-mean amplitudes.
    The shapes of the projected arrays need to be multiples of the shape of the amplitudes.
    The motivation for this projector is to enforce a measurement constraint on
    an array with finer sampling than the detector pixels.
    """

    def __call__(self, u, t=0.0):
        if u.shape[0] % self.amplitude.shape[0] or u.shape[1] % self.amplitude.shape[1]:
            raise RuntimeError(
                f"data shape ({u.shape}) is not divisible by amplitude shape ({self.amplitude.shape})"
            )
        sampling1 = u.shape[0] // self.amplitude.shape[0]
        sampling2 = u.shape[1] // self.amplitude.shape[1]
        out = u.clone()
        blocks = out.unfold(-1, sampling2, sampling2).unfold(-3, sampling1, sampling1)
        mean_amplitude = (blocks.abs() ** 2).mean((-2, -1)).sqrt()
        blocks *= (self.amplitude / mean_amplitude)[:, :, None, None]
        # set value for blocks with 0 amplitude (there, phase is set to zero)
        blocks[mean_amplitude == 0, :, :] = self.amplitude[mean_amplitude == 0][
            :, None, None
        ].cfloat()
        return out


class AmplitudeThreshold(ConstraintOperator):
    """
    (Complex) wave function amplitude range projections. If wave function exceeds given thresholds its value it
    projected onto the corresponding threshold.

    For example use `AmplitudeThreshold(0.9, 1)` for allowance of up to 10% absorption.
    """

    def __init__(self, min, max):
        """Thresholds for amplitude. min/max can be None as placeholder for inf."""
        self.min = as_tensor(min)
        self.max = as_tensor(max)

    def __call__(self, u: Tensor, t=0.0):
        amp = abs(u)
        phase = angle(u)

        amp = clip(amp, self.min, self.max)

        return amp * exp(1j * phase)


class PhaseClip(ConstraintOperator):
    """
    Threshold projector for phase of complex wavefield (amp * exp(i*phase)) into [min, max] range.
    """

    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def __call__(self, u, t=0):
        phase = angle(u)
        phase_new = clip(phase, self.min, self.max)

        return abs(u) * exp(1j * phase_new)


class HomogeneityConstraint(ConstraintOperator):
    def __init__(self, betadelta):
        self.betadelta = betadelta

    def __call__(self, u, t=None):
        phase = angle(u)
        return exp((1j - self.betadelta) * phase)


class Constraints(ConstraintOperator):
    """
    Setup constraints for reconstruction of refractive objects, i.e. the exponent of an exponential.

    Example
    -------
    Negativity constrain:
    >>> constraints = Constraints(phase_max=0.0)

    Notes
    -----
    This constraints object does not work for AP reconstructions.
    """

    def __new__(cls, phase_min: float = None, phase_max: float = None, support: ndarray = None):
        ops = []

        if support is not None:
            ops.append(SupportOp(support))
        if phase_max is not None or phase_min is not None:
            ops.append(BoundOp(min=phase_min, max=phase_max))

        if ops:
            return reduce(cls.__mul__, ops)
        else:
            return IdentityOp()


class WaveConstraints(ConstraintOperator):
    """
    Constraints wrapper for (complex) wavefields, e.g. used in AP.
    """

    def __new__(cls, betadelta=None, phase_min=None, phase_max=None, support=None):
        ops = []

        if support is not None:
            ops.append(SupportOp(support))
        if phase_min is not None or phase_max is not None:
            ops.append(PhaseClip(min=phase_min, max=phase_max))
        if betadelta is not None:
            if betadelta == 0.0:
                # no absorption, wavevfield has constant amplitude everywhere
                ops.append(AmplitudeProjector(1.0))
            else:
                ops.append(HomogeneityConstraint(betadelta))

        if ops:
            return reduce(cls.__mul__, ops)
        else:
            return IdentityOp()
