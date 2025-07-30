"""
Author: Jens Lucht
"""

from numpy import ndarray, newaxis
from torch import ones, as_tensor

from ..optimize import AlternatingProjections
from .propagation import FresnelTFPropagator
from .constraints import AmplitudeProjector, ConstraintOperator, WaveConstraints


class AP:
    """Alternating projections for holographic phase retrieval."""

    algorithm = AlternatingProjections

    def __init__(
        self,
        shape,
        fresnel_nums,
        ndim=2,
        dtype=None,
        device=None,
    ):
        self.dtype = dtype
        self.device = device
        self.ndim = ndim

        self.propagator = FresnelTFPropagator(
            shape,
            fresnel_nums,
            dtype=dtype,
            device=device,
            keep_type=False,
        )

    def __call__(
        self,
        holograms,
        constraints=None,
        initial_guess=None,
        max_iter: int = 100,
        keep_type=False,
    ):
        """Reconstruct holograms.

        Parameters
        ----------
        holograms :
            Intensities measured at detector.
        constraints :
            Constraints projectors for object/sample. Default Amplitude = 1 constrain for pure-phase object.
        max_iter : int, Optional
            Maximal number of iterations.
        """
        holograms_t = type(holograms)
        holograms = as_tensor(holograms, device=self.device)
        shape = holograms.shape[-self.ndim :]

        # if single image is entered expand to stack of one image
        single_image = holograms.ndim == self.ndim
        if single_image:
            holograms = holograms[newaxis]

        projector_holos = AmplitudeProjector(holograms.sqrt())
        projector_object = (
            constraints if constraints is not None else WaveConstraints(betadelta=0.0)
        )

        # ensure correct device placement
        if isinstance(projector_object, ConstraintOperator):
            projector_object.to_device(self.device)

        # initialize with plane wave (ones) or initial guess if given
        if initial_guess is None:
            x = ones(shape, device=self.device, dtype=holograms.dtype)
        else:
            x = as_tensor(initial_guess, device=self.device)

        # AP
        ap = self.algorithm(
            self.propagator,
            (projector_object, projector_holos),
            x,
            max_iter=max_iter,
        )

        # iterate util stopping condition is met
        while not ap.done():
            ap.step()

        # recast into numpy if requested
        if keep_type and holograms_t is ndarray:
            out = ap.x.cpu().numpy()
        else:
            out = ap.x

        # remove stack axis if single image
        if single_image:
            out = out[0]

        return out
