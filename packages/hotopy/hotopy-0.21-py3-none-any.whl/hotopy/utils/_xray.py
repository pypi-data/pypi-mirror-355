"""
==================================================
X-ray physics little helpers (:mod:`hotopy.xray`)
==================================================

.. currentmodule:: hotopy.xray

.. autosummary::
    :toctree: generated/

    wavelength_energy
    n_delta_beta

"""

from numpy import asarray, real, imag


def wavelength_energy(E):
    """
    Converts energy E (in keV) to wavelength (in m)

    Parameters
    ----------
    E: float
        Energy in keV

    Returns
    -------
    Wavelength in SI unit m.
    """
    wl = 12.398 / E  # in A = 10^-10 m
    return wl * 1e-10  # m


def n_delta_beta(n):
    r"""
    Converts complex refractive index to delta, beta values, i.e.

    .. math:: n = 1 - \delta + i \beta

    to

    .. math:: \delta = 1 - \Re(n), \beta = \Im(n)

    Parameters
    ----------
    n: complex, array-like
        Complex refractive indices. Can be scalar or list.

    Returns
    -------
    delta, beta:
        Phase shift and linear attenuation coefficient
    """
    n = asarray(n)
    delta = 1 - real(n)
    beta = imag(n)
    return delta, beta
