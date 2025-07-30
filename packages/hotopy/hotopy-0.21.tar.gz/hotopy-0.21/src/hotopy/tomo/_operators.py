"""
Operators acting on numpy arrays

See also: hotopy.holo.constraints for constraint operators on torch tensors.
"""

from __future__ import annotations
import abc
from numpy import ndarray, asarray, clip
from numpy.typing import ArrayLike
from functools import reduce


class Operator(abc.ABC):
    @abc.abstractmethod
    def __call__(self, arr: ArrayLike) -> ArrayLike:
        return

    def __mul__(self, other: Operator) -> Operator:
        return OperatorComposition(self, other)


class OperatorComposition(Operator):
    def __init__(self, left: Operator, right: Operator) -> None:
        self._left = left
        self._right = right

    def __call__(self, x: ArrayLike) -> ArrayLike:
        return self._left(self._right(x))


class IdentityOperator(Operator):
    def __call__(self, x: ArrayLike) -> ArrayLike:
        return x


class MaskedOperator(Operator):
    """Restricted operator that only acts on the data contained in the mask."""

    def __init__(self, mask: ArrayLike, operator: Operator) -> None:
        self.mask = asarray(mask, dtype=bool)
        self.op = operator

    def __call__(self, u: ArrayLike) -> ndarray:
        return self.op(u) * self.mask + u * ~self.mask


class SupportOperator(Operator):
    def __init__(self, support: ArrayLike) -> None:
        self.support = asarray(support, dtype=bool)

    def __call__(self, x: ArrayLike) -> ndarray:
        # check if x has batch dimensions (in first axes) and expand mask accordingly
        # to enable broadcasting
        if x.ndim > self.support.ndim:
            support = self.support[(*(None,) * (x.ndim - self.support.ndim), ...)]
        else:
            support = self.support
        return support * x


class ClipOperator(Operator):
    def __init__(self, vmin: None | float = None, vmax: None | float = None) -> None:
        self.vmin = vmin
        self.vmax = vmax

    def __call__(self, x: ArrayLike) -> ndarray:
        return clip(x, self.vmin, self.vmax)


class Constraints(Operator):
    """
    Setup constraints for numpy arrays.

    Example
    -------
    Negativity constraint:
    >>> constraints = Constraints(max=0.0)

    Notes
    -----
    See also: hotopy.holo.constraints for constraint operators on torch tensors
    """

    def __new__(
        cls,
        vmin: float | None = None,
        vmax: float | None = None,
        support: ArrayLike | None = None,
        mask: ArrayLike | None = None,
    ) -> Operator:
        ops = []

        if support is not None:
            ops.append(SupportOperator(support))
        if vmax is not None or vmin is not None:
            ops.append(ClipOperator(vmin, vmax))
        if ops:
            op = reduce(cls.__mul__, ops)
            if mask is not None:
                return MaskedOperator(mask, op)
            return op
        else:
            return IdentityOperator()
