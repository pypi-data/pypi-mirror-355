"""
======================================
Image processing (:mod:`hotopy.image`)
======================================


Statistical functions
---------------------

.. autosummary::
    :toctree: generated/

    radial_power_spectrum


Transformation
--------------

.. autosummary::
    :toctree: generated/

    imscale
    imshift
    imshiftscale


Filtering and windowing functions
---------------------------------

.. autosummary::
    :toctree: generated/

    GaussianBlur
    GaussianBandpass
    gaussian_filter
    gaussian_bandpass2_real
    MedianFilter2d
    remove_outliers
    ndwindow
    dissect_levels


Generators and phantoms
-----------------------

.. autosummary::
    :toctree: generated/

    ball_projection
    ball
    ndgaussian

..
    author: Jens Lucht
"""

from ._filter import (
    ndwindow,
    gaussian_filter,
    gaussian_bandpass2_real,
    dissect_levels,
    split_freqs,
    FourierFilter,
    GaussianBlur,
    GaussianBandpass,
    MedianFilter2d,
    remove_outliers,
)
from ._generators import ndgaussian, ball, ball_projection
from ._stats import radial_power_spectrum, fourier_shell_correlation, radial_profile
from ._transforms import (
    imscale,
    imshift,
    imshiftscale,
    affine_transform2D,
    to_polar2D,
    AveragePool2d,
)
from ._registration import register_images
from ._inpainting import InpaintMinimalCurvature


__all__ = [
    # filter
    "ndwindow",
    "gaussian_filter",
    "gaussian_bandpass2_real",
    "dissect_levels",
    "split_freqs",
    "FourierFilter",
    "GaussianBlur",
    "GaussianBandpass",
    "MedianFilter2d",
    "remove_outliers",
    # generators
    "ndgaussian",
    "ball",
    "ball_projection",
    # stats
    "radial_power_spectrum",
    "fourier_shell_correlation",
    "radial_profile",
    # transforms
    "imscale",
    "imshift",
    "imshiftscale",
    "affine_transform2D",
    "to_polar2D",
    "AveragePool2d",
    # registration
    "register_images",
    # inpainting
    "InpaintMinimalCurvature",
]
