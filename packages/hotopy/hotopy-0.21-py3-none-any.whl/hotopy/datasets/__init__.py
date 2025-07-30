"""
=========================================
Example datasets (:mod:`hotopy.datasets`)
=========================================

Experimental holographic datasets
---------------------------------
.. autosummary::
    :toctree: generated/

    beads
    radiodurans
    macrophage
    world_holograms
    spider

Example:

    >>> from hotopy.datasets import beads
    >>> data = beads()
    >>> # list content
    >>> print(list(data.keys()))   # ['holograms', 'fresnelNumbers']

    Some dataset also have a ``'support'`` field, which can be used for constrained phase retrieval.

    >>> holos, fresnel_nums = data["holograms"], data["fresnelNumbers"]
    >>> print(holos.shape, fresnel_nums.shape)

    This datasets can be used for phase retrieval, e.g. with CTF or Tikhonov.

    >>> from hotopy.holo import Tikhonov
    >>> imshape = holos.shape[-2:]
    >>> alpha = [0, 5e-2]
    >>> betadelta = 0.01  # 1% effective absorption
    >>> device = "cpu"  # if CUDA cards are available set ``device="cuda"``.
    >>> tik = Tikhonov(imshape, fresnel_nums, betadelta=betadelta, alpha=alpha, device=device)
    >>> rec_tik = tik(holos).cpu().numpy()


Simulation phantoms
-------------------
.. autosummary::
    :toctree: generated/

    dicty
    dicty_multi
    world

.. author: Jens Lucht, 2023-2024
"""

from ._holograms import (
    beads,
    radiodurans,
    macrophage,
    world_holograms,
    spider,
    logo_holograms,
    catparticle,
)
from ._phantoms import dicty, dicty_multi, world, balls, checkerboard

__all__ = [
    "beads",
    "radiodurans",
    "macrophage",
    "world_holograms",
    "logo_holograms",
    "catparticle",
    "spider",
    "dicty",
    "dicty_multi",
    "world",
    "balls",
    "checkerboard",
]
