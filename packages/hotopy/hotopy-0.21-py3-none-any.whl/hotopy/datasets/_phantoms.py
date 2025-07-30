"""
.. autosummary::
    :toctree: generated/


.. author: Jens Lucht, 2023
"""

from ._fetcher import fetcher
from ..image import dissect_levels, ball
import numpy as np
from functools import reduce


def _simple_phantom(name):
    cnt = fetcher(f"phantom_{name!s}.npz")
    return cnt["phantom"]


def dicty():
    return _simple_phantom("dicty")


# not an actual dataset, but simple wrapper to get a multi-component/material phantom
def dicty_multi(*lims):
    """
    Multi-component/material ``dicty`` phantom.

    See dissect_levels, dicty
    """
    im = dicty()
    return dissect_levels(im, *lims)


def world():
    return _simple_phantom("world").astype(float)


def world_uint():
    # dataset in original datatype
    return _simple_phantom("world")


def _get_default_cen_rad_dens(shape=(120, 128, 128)):
    ref_length_radii = min(shape)
    height = shape[0]
    dist_center = 0.7 * min(shape[1:]) / 2

    centers, radii, densities = [], [], []
    for z, phi in zip(
        ((0.3 * height,) * 3 + (0.7 * height,)),
        2 * np.pi * np.array((0, 0.25, 0.5, 0.25)),
        strict=True,
    ):
        radii.append(ref_length_radii / 15)
        centers.append((z, dist_center, phi))  # z, r, phi
        densities.append(1)

    for i, phi in enumerate(2 * np.pi * np.arange(0, 1, 1 / 12)[:-1]):
        radii.append(ref_length_radii * np.sqrt(i + 1) / 60)
        centers.append((0.5 * height, dist_center, phi))  # z, r, phi
        densities.append(2 / np.sqrt(i + 1))

    centers = np.array(centers)
    # centers: r, phi -> x, y
    r, phi = centers[:, 1:].T
    centers[:, 1:] = np.stack(
        (shape[1] / 2 + r * np.cos(phi), shape[2] / 2 + r * np.sin(phi)), axis=-1
    )
    return centers, radii, densities


def balls(shape=(120, 128, 128), centers=None, radii=None, densities=1, dtype=np.float32):
    """generate a volume containing balls of uniform density.
    The default values yield an example volume for tomography.
    """
    # preprocess parameters
    if centers is None:
        if len(shape) == 3:
            centers, radii, densities = _get_default_cen_rad_dens(shape)
        else:
            rng = np.random.default_rng(seed=0)
            centers = shape * rng.random((10, len(shape)))
    else:
        centers = np.asarray(centers)
    if radii is None:
        radii = min((min(shape) / 2, sum(shape) / len(shape) / 10))
    radii = np.broadcast_to(radii, len(centers))
    densities = np.broadcast_to(densities, len(centers))

    # generate phantom
    phantom = np.zeros(shape, dtype=dtype)
    for r, cen, d in zip(radii, centers, densities, strict=True):
        r_px = int(r)
        cen_px = cen.astype(int)
        slc = tuple(  # roi in phantom
            slice(
                max(0, c_px - r_px),
                c_px + r_px + 2,
            )
            for c_px in cen_px
        )
        slc_ball = tuple(  # crop ball at borders of phantom
            slice(
                max(0, r_px - c_px),
                r_px + s - c_px,
            )
            for s, c_px in zip(shape, cen_px, strict=True)
        )
        phantom[slc] += d * ball(len(shape) * (2 * r_px + 2,), r, center=r_px + cen % 1)[slc_ball]
    return phantom


def checkerboard(shape, boxsize=1):
    ndim = len(shape)
    boxsize = np.broadcast_to(boxsize, ndim)
    coordinates = np.indices(shape)
    stripes = (coordinates / (2 * np.expand_dims(boxsize, tuple(range(1, ndim + 1))))) % 1
    stripes = (coordinates / boxsize[(slice(None),) + ndim * (None,)]) % 2 >= 1
    return reduce(np.logical_xor, stripes)
