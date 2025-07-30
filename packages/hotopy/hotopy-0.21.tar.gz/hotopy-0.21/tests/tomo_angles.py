# %% test angles

# verify that tomo.angles reflects the angles used in creation

import numpy as np
import matplotlib.pyplot as plt
from hotopy import tomo
from itertools import product

def min_dist(angles1, angles2):
    return (angles1 - angles2 + np.pi) % (2 * np.pi) - np.pi

def angles_close(angles1, angles2, atol=1e-5):
    return np.allclose(min_dist(angles1, angles2), 0, atol=atol)

np.random.seed(1234)
z01, z02, px = 99, 100, 1

for cone, det_shape, angles_in in product(
    (
        (z01, z02, px),
        None,
    ), (
        (10, ),
        (11, 11),
    ), (
        2 * np.pi * np.random.random(12),
        # np.pi * np.linspace(-1, 1, 12)[:-1],
        # np.pi * np.linspace(1, -1, 12)[1:],
    )
):
    t = tomo.setup(det_shape, angles_in, cone=cone)
    print(t.p_geometry["type"])
    angles_in = angles_in % (2 * np.pi)

    def verify(angles_out):
        if not angles_close(angles_in, angles_out):
            plt.figure()
            plt.plot(angles_in, label='in')
            plt.plot(angles_out, label='out')
            plt.plot(min_dist(angles_in, angles_out), label="diff")
            plt.legend()
            plt.title(t.p_geometry["type"])
            # print(min_dist(angles_in, angles_out))
            raise ValueError("output angles dont fit")

    verify(t.angles)

    t.apply_shift(0)  # forces vector geometry
    verify(t.angles)

# %%
