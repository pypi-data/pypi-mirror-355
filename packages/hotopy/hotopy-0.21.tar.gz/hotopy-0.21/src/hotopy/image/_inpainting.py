"""
.. author:: Jens Lucht
"""

import numpy as np
from scipy.sparse import csr_array, vstack as spvstack
from scipy.sparse.linalg import spsolve


def forward_diff_operator(shape, axis, dtype=None, device=None):
    shape = np.atleast_1d(shape)
    n = np.prod(shape, dtype=int)

    offset = np.prod(
        shape[axis + 1 :], dtype=int
    )  # offset to difference neighbor (remark: prod([]) = 1)
    r = np.arange(n - offset)  # rows
    c = np.arange(offset, n)  # forward difference neighbors (without wrap around)

    # mask out boundaries
    mask = (np.arange(offset, n) // offset) % shape[axis] > 0
    r = r[mask]
    c = c[mask]

    # setup sparse matrix
    data = np.ones(2 * len(r), dtype=dtype)
    data[: len(r)] = -1
    rows = (*r, *r)
    cols = (*r, *c)
    coords = (rows, cols)
    A = csr_array((data, coords), shape=(n, n), dtype=dtype)

    return A


class InpaintMinimalCurvature:
    """
    Inpaint image by minimal curvature.

    Setups callable minimal curvature inpainting algorithm for given dimensions and mask.
    Use with: ``img_inpainted = InpaintMinimalCurvature(img.shape, mask)(img)``

    Parameters
    ----------
    imshape: tuple
        Shape of image to inpaint.
    mask: array_like
        Boolean array in shape ``imshape`` which is true, where image is to be inpainted.
    dtype:
        Datatype for operators.
    device:
        Ignored so far.

    Returns
    -------
    f: Callable
        Inpainting instance. Use with ``f(img)``.
    """

    def __init__(self, imshape, mask, dtype=None, device=None):
        imshape = np.atleast_1d(imshape)
        n = np.prod(imshape)
        dims = len(imshape)
        mask = np.asarray(mask, dtype=bool)

        assert dims == 2, NotImplementedError(
            f"{self.__class__.__name__} arrays needs to be two dimensional."
        )

        # (forward) Hessian operator
        dx = forward_diff_operator(imshape, 1, dtype=dtype)
        dy = forward_diff_operator(imshape, 0, dtype=dtype)
        H = spvstack([dx.T @ dx, dx.T @ dy, dy.T @ dx, dy.T @ dy])

        # embedding of pixel to inpaint
        inpaint_indices = np.flatnonzero(mask)  # coordinated in flatted coordinates
        m = len(inpaint_indices)  # number of pixel to inpaint (size of mask)
        inpaint_keys = np.arange(m)  # some representations keys
        embed_data = np.ones(m)
        S = csr_array((embed_data, (inpaint_indices, inpaint_keys)), shape=(n, m), dtype=dtype)

        # setup curvature forward operator
        A = H @ S
        AtA = A.T @ A

        self.mask = mask
        self.H = H
        self.S = S
        self.A = A
        self.AtA = AtA

    def __call__(self, img, out=None):
        img_masked = (~self.mask) * img
        b = self.A.T @ (self.H @ img_masked.ravel())

        # solve with least squares (minimal curvature)
        x = -spsolve(self.AtA, b)

        if out is None:
            out = np.copy(img)
        out[self.mask] = x

        return out, x
