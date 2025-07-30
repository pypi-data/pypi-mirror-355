# %%
# remarks

# shape of projections:
#     (nangles, height, width)
#     (nangles, width)

# shape of volumes:
#     (width, width)
#     (height, width, width)

# %%
import numpy as np
import matplotlib.pyplot as plt
from hotopy.tomo import *
import astra
astra.astra.set_gpu_index(1)

import napari
v = napari.Viewer()
show_image = v.add_image

# %% phantom
from hotopy.datasets import balls
det_shape = height, width = (120, 128)
phantom = balls((height, width, width))
show_image(phantom)

# %% geometry
numangles = int(1.5 * width)
# angles = 2 * np.pi * np.linspace(-0.5, 0.5, numangles) * (1 -1 / numangles)
angles = np.linspace(0, 2 * np.pi, numangles + 1)[:-1]
z01, z02, px = 99, 100, 1
cone = (z01, z02, px)

def test_tomo(t, phantom=phantom, it=1):
    projections = t.project(phantom)
    show_image(projections)

    vol_reco = t.reconstruct(iterations=it)
    show_image(vol_reco)

    assert projections.shape in ((numangles, height, width), (numangles, width))
    assert vol_reco.shape in ((height, width, width), (width, width))

    return projections, vol_reco

# %% test 2d
t = tomo.setup(det_shape[-1], angles)
projections = t.project_stack(phantom, link=False)
#%%
show_image(phantom)
# %% test 3d
t = tomo.setup(det_shape, angles, cone=cone)
projections = t.project(phantom)
show_image(projections)

reco = t.reconstruct()
show_image(reco)

projections[()] = 0
reco = t.reconstruct()
show_image(reco)