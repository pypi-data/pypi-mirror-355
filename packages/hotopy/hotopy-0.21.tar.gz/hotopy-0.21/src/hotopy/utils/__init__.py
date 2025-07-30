"""
===========================================
Utilities and helpers (:mod:`hotopy.utils`)
===========================================

Fourier transforms and helpers
------------------------------
.. autosummary::
    :toctree: generated/

    fftfreqn
    rfftfreqn
    rfftshape
    fftflip
    ZoomFFTN


Padding
-------
.. autosummary::
    :toctree: generated/

    Padder


Conversions
-----------
.. autosummary::
    :toctree: generated/

    n_delta_beta
    wavelength_energy


Input/output functions
----------------------
.. autosummary::
    :toctree: generated/

    read_matlab_raw
    save_matlab_raw


..
    author: Jens Lucht, 2022-2024
"""

from .fourier import fftfreqn, fftgridn, rfftfreqn, rfftshape, fftflip, ZoomFFTN
from ._io import read_matlab_raw, save_matlab_raw
from ._misc import enable_debug_logging, gridn, expand_to_dim
from ._padding import Padder, pad_width_to_torch, crop_quadratic, crop_to_shape
from ._xray import n_delta_beta, wavelength_energy

__all__ = [
    "fftfreqn",
    "fftgridn",
    "rfftfreqn",
    "rfftshape",
    "fftflip",
    "ZoomFFTN",
    "read_matlab_raw",
    "save_matlab_raw",
    "enable_debug_logging",
    "gridn",
    "expand_to_dim",
    "Padder",
    "pad_width_to_torch",
    "crop_quadratic",
    "crop_to_shape",
    "n_delta_beta",
    "wavelength_energy",
]
