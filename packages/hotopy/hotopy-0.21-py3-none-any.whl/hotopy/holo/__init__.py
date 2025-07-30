"""
=========================================================
Holographic phase retrieval methods (:mod:`hotopy.holo`)
=========================================================

.. currentmodule:: hotopy.holo


Submodules
==========

.. autosummary::
    :toctree: generated/

    propagation


(Deep) Holographic regime phase retrieval
-----------------------------------------

For Fresnel numbers << 1 and monochromatic sources, e.g. at synchrotrons.

.. autosummary::
    :toctree: generated/

    CTF
    Tikhonov
    TikhonovTV
    AP
    ICT


Transport of Intensity Equation based methods (TIE)
---------------------------------------------------

Transport of Intensity (TIE) used for laboratory X-ray sources.

.. autosummary::
    :toctree: generated/

    BronnikovAidedCorrection
    ModifiedBronnikov
    Paganin
    GeneralizedPaganin


Propagation methods
-------------------

Convenience imports from ``propagation`` submodule.

.. autosummary::
    :toctree: generated/

    simulate_hologram

Helpers
-------

.. autosummary::
    :toctree: generated/

    Constraints
    rescale_defocus_series
    rescale_defocus_fresnel_numbers
    twolevel_regularization
    ctf_erf_filter
    erf_filter
    find_fresnel_number
    pca_decompose_flats
    pca_synthesize_flat
"""

from .propagation import (
    FresnelTFPropagator,
    simulate_hologram,
    expand_fresnel_numbers,
)
from .constraints import Constraints, WaveConstraints
from ._tieregime import BronnikovAidedCorrection, ModifiedBronnikov, Paganin, GeneralizedPaganin
from ._ctf import CTF
from ._tikhonov import Tikhonov, TikhonovTV, nonlinearity_low_freq_correction
from ._ap import AP
from ._pbi import ICT
from .regularization import erf_filter, ctf_erf_filter, twolevel_regularization
from ._util import (
    check_fresnel_number,
    rescale_defocus_series,
    rescale_defocus_fresnel_numbers,
    find_fresnel_number,
    difference_fresnel_numbers,
    flatfield_inpainting_correction,
)
from ._pca import pca_decompose_flats, pca_synthesize_flat, pca_decompose_arpack

__all__ = [
    "FresnelTFPropagator",
    "simulate_hologram",
    "expand_fresnel_numbers",
    "BronnikovAidedCorrection",
    "ModifiedBronnikov",
    "Paganin",
    "GeneralizedPaganin",
    "CTF",
    "Tikhonov",
    "TikhonovTV",
    "ICT",
    "AP",
    "Constraints",
    "WaveConstraints",
    "nonlinearity_low_freq_correction",
    "erf_filter",
    "ctf_erf_filter",
    "twolevel_regularization",
    "check_fresnel_number",
    "rescale_defocus_series",
    "rescale_defocus_fresnel_numbers",
    "find_fresnel_number",
    "difference_fresnel_numbers",
    "flatfield_inpainting_correction",
    "pca_decompose_flats",
    "pca_synthesize_flat",
    "pca_decompose_arpack",
]
