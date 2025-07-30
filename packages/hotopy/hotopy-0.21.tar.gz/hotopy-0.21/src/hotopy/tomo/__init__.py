"""
========================================
Tomographic methods (:mod:`hotopy.tomo`)
========================================

The tomography methods are based on wrappers of the ASTRA Toolbox, a MATLAB and
Python toolbox of high-performance GPU primitives for 2D and 3D tomography [1]_, [2]_.

.. currentmodule:: hotopy.tomo

Geometry
--------

The standard geometries assumes a sample rotating around the axis pointing up, measured
in radian.

The wrappers support full use of ASTRA's vector geometries. For each projection, detector
position and orientation as well as the ray direction (in parallel geometries) or
source position (in cone geometries) can be thus be specified individually.


Tomographic reconstruction
--------------------------
ASTRA wrappers are only available if the ``astra-toolbox`` package is correctly installed.

.. autosummary::
    :toctree: generated/

    setup
    AstraTomo2D
    AstraTomo3D
    algorithm_config

    ReprojectionAlignment



Ring removal
------------
.. autosummary::
    :toctree: generated/

    ringremove
    ringremove_additive
    ringremove_wavelet


Tomographic corrections and alignment
-------------------------------------
.. autosummary::
    :toctree: generated/

    find_sample_rotaxis_shift
    sample_rotaxis_shift_correlation


Consistency checks
------------------
.. autosummary::
    :toctree: generated/

    hlcc


Notes on tomographic geometries
-------------------------------

- angles measure rotation of the sample around the axis pointing up (in radians, opposite of astra)

- shape of projections:

  .. code-block::

    (            #          orientation for angle=0, looking from source to detector
        nangles, #          -
        height,  # (if 3d)  top -> bottom
        width,   #          left -> right
    )

- shape of volumes:

  .. code-block::

    (           #          orientation for angle==0, looking from source to detector
        height, # (if 3d)  top -> bottom
        width,  #          front -> back (src -> det)
        width,  #          left -> right
    )


The ASTRA code uses the following (3d)

  - angles measure rotation of source and detector around the axis pointing up

  - shape of projection

  .. code-block::

    (            #         orientation at angle==0, looking from source to detector
        height,  # (if 3d) top -> bottom
        angles,  #         -
        width,   #         left -> right
    )


  - shape of volume

  .. code-block::

    (           # orientation at angle==0, looking from source to detector
        height, # (if 3d) top -> bottom
        width,  #         for 3d: back -> front (det -> src)
                #         for 2d: front -> back (src -> det)
        width,  #         left -> right
    )



References
----------

.. [1] http://www.astra-toolbox.com
.. [2] https://github.com/astra-toolbox/astra-toolbox
"""

from logging import getLogger

from ._alignment import (
    hlcc,
    find_sample_rotaxis_shift,
    sample_rotaxis_shift_correlation,
    register_sinogram,
)
from ._ringremove import ringremove, ringremove_wavelet, ringremove_additive
from ._operators import Constraints


logger = getLogger(__name__)

# only load astra-depended methods if astra is available
try:
    from astra import set_gpu_index
    from ._astra import (
        AstraTomo2D,
        AstraTomo3D,
        setup,
        algorithm_config,
    )
    from ._reprojection_alignment import ReprojectionAlignment

    __has_astra__ = True
    logger.info(f"Loaded {__name__} with ASTRA sub-module")
except ModuleNotFoundError as err:
    __has_astra__ = False
    logger.warning(
        f"Could not import 'astra' package for tomographic operations. See https://astra-toolbox.com for installation "
        f"guidance."
        f"Loaded {__name__} without ASTRA sub-module. ASTRA-depended functions are not available."
    )
    logger.debug(err)


__all__ = [
    # alignment
    "hlcc",
    "find_sample_rotaxis_shift",
    "sample_rotaxis_shift_correlation",
    "register_sinogram",
    # ringremove
    "ringremove",
    "ringremove_additive",
    "ringremove_wavelet",
    "Constraints",
]

if __has_astra__:
    __all__ += [
        "set_gpu_index",
        "AstraTomo2D",
        "AstraTomo3D",
        "setup",
        "algorithm_config",
        "ReprojectionAlignment",
    ]
