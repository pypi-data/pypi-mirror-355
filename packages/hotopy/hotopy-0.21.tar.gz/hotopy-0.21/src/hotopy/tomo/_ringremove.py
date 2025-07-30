import numpy as np
from scipy import ndimage
import ptwt
import torch
from torch import cuda


def ringremove(sino, type="additive", **kwargs):
    """
    Removes ring artifacts in tomographic reconstructions by reducing the amount of
    horizontal lines in the given sinogram. Ring removal is either based on the method
    proposed by Ketcham et al. [1]_, denoted as 'additive', or on the method proposed
    by Muench et al. [2]_, denoted as 'wavelet'.

    Parameters
    ----------
    sino : array-like (angles x width) or (angles x height x width)
        sinogram
    type : "additive" or "wavelet"
    **kwargs
        Parameters to be passed to one of the following functions:
        * ringremove_additive()
        * ringremove_wavelet()

    References
    ----------
    .. [1]
        Richard A. Ketcham "New algorithms for ring artifact removal", Proc. SPIE 6318,
        Developments in X-Ray Tomography V, 63180O (7 September 2006);
        :doi: `10.1117/12.680939`
    .. [2]
        Beat Münch, Pavel Trtik, Federica Marone, and Marco Stampanoni, "Stripe and ring artifact
        removal with combined wavelet — Fourier filtering," Opt. Express 17, 8567-8591 (2009)
        :doi:`10.1364/OE.17.008567`
    """
    if type == "none":
        return sino
    elif type == "additive":
        return ringremove_additive(sino, **kwargs)
    elif type == "wavelet":
        return ringremove_wavelet(sino, **kwargs)
    else:
        raise ValueError(f"no ringremoval method of type {type} found")


def ringremove_additive(sino, smoothing="mean", filter_size=9, mask=None, strength=1):
    """
    Remove rings in sinogram by reducing non-smooth components from the mean signal
    of the detector row.

    Parameters
    ----------
    sino : array-like (angles x width) or (angles x height x width)
        sinogram
    smoothing : {"mean", "median", "gauss"}
        Type of the smoothing filter. Defaults to "median".
    filter_size : int (optional)
        Size of the smoothing filter. Defaults to 9. For Gaussian filtering, sigma = filter_size / 3 is chosen.
    mask : (optional)
        Mask determining where to apply the corrections.
    strength : int (optional)
        Parameter to modify the strength of the correction. Defaults to 1.
    """
    out_dim = sino.ndim
    if sino.ndim == 2:
        sino = sino[:, None, :]

    sino_mean = sino.mean(axis=0)
    if smoothing == "mean":
        sino_mean_smooth = ndimage.uniform_filter(sino_mean, size=(1, filter_size))
    elif smoothing == "median":
        sino_mean_smooth = ndimage.median_filter(sino_mean, size=(1, filter_size))
    elif smoothing == "gauss":
        sino_mean_smooth = ndimage.gaussian_filter1d(sino_mean, sigma=filter_size / 3, axis=1)
    else:
        raise ValueError('Choose between "mean", "median" and "gauss" for smoothing')

    correction = sino_mean - sino_mean_smooth
    if mask is not None:
        correction[~mask] = 0
    result = sino - strength * correction

    if out_dim == 3:
        return result
    else:
        return result[:, 0]


def ringremove_wavelet(
    sino, wavelet="sym8", level=3, sigma=1, inplace=False, device=None, batchsize=10
):
    """
    Remove rings in sinogram by filtering vertical components of a wavelet decomposition.

    Parameters
    ----------
    sino : array-like (angles x width) or (angles x height x width)
        sinogram
    wavelet : Wavelet object or name string (optional)
        Type of the wavelet decomposition. See pywt.dwt2 for details. Defaults to "sym8"
    level : int (optional)
        Number of wavelet decomposition steps. Defaults to 3.
    sigma : float (optional)
        Width of the filter. Defaults to 1.
    """
    if device is None:
        device = "cuda" if cuda.is_available() else "cpu"

    out_dim = sino.ndim

    if sino.ndim == 2:
        sino = sino[:, None, :]

    if inplace:
        sino_out = sino
    else:
        if isinstance(sino, torch.Tensor):
            sino_out = torch.empty_like(sino)

            def out_transform(x):
                return x

        else:
            sino_out = np.empty_like(sino)

            def out_transform(x):
                return torch.as_tensor(x).cpu()

    for batchstart in range(0, sino_out.shape[1], batchsize):
        sino_slice = torch.as_tensor(sino[:, batchstart : batchstart + batchsize], device=device)
        sino_slice = sino_slice.permute((1, 0, 2))  # move batch axis (vertical) to first index

        # wavelet decomposition
        coeffs = []
        shapes = []
        for _ in range(level):
            shapes.append(sino_slice.shape)
            sino_slice, c = ptwt.wavedec2(sino_slice, wavelet, level=1)
            coeffs.append(c)
        # filter components
        for i, (cH, cV, cD) in enumerate(coeffs):
            # analog to matlab
            k = torch.fft.rfftfreq(cV.shape[1], 1 / cV.shape[1])
            filt = 1 - torch.exp(-0.5 * k**2 / sigma**2)[:, None].to(device=device)
            cVFou = torch.fft.rfft(cV, axis=1)
            cV = torch.fft.irfft(cVFou * filt, cV.shape[1], axis=1)
            coeffs[i] = (cH, cV, cD)

        # much shorter alternative for filtering, dont know, why the scaling (10/sigma) is like that
        # coeffs[i] = (cH, cV - ndimage.gaussian_filter1d(cV, 100/sigma, axis=0), cD)

        # wavelet reconstruction
        for c, s in zip(reversed(coeffs), reversed(shapes), strict=True):
            sino_slice = ptwt.waverec2((sino_slice, c), wavelet=wavelet)
            sino_slice = sino_slice[:, : s[1], : s[2]]
        sino_out[:, batchstart : batchstart + batchsize] = out_transform(
            sino_slice.permute((1, 0, 2))
        )

    if out_dim == 3:
        return sino_out
    else:
        sino = sino[:, 0]
        return sino_out[:, 0]
