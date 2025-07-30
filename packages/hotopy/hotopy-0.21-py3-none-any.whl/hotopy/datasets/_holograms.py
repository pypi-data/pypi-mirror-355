"""
.. autosummary::
    :toctree: generated/

.. author: Jens Lucht, 2024
"""

from ._fetcher import fetcher
from ._fetcher import _decompress_npz


def _simple_holograms(name):
    return fetcher(f"holograms_{name!s}.npz")


def radiodurans():
    return _simple_holograms("radiodurans")


def beads():
    return _simple_holograms("beads")


def macrophage():
    return _simple_holograms("macrophage")


def world_holograms():
    return _simple_holograms("world")


def spider():
    """
    Single-distance dataset for direct contrast aka TIE regime phase retrieval.
    """
    return _simple_holograms("spider")


def logo_holograms():
    """
    deep-holographic dataset
    """
    return _simple_holograms("logo")


def catparticle():
    """
    Normalized holographic projections (holograms) at two defocus positions of a
    catalytic nano-particle in the deep-holographic regime.
    This dataset is at a single tomographic angle.

    For the full tomographic dataset see https://doi.org/10.25625/CQ1EKY
    """
    return fetcher("holograms_catparticle.npz.bz2", processor=_decompress_npz)
