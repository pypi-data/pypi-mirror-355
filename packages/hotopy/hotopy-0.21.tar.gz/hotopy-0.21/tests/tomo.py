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
from hotopy import tomo
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

# %% test fdk
t = tomo.setup(det_shape, angles, cone=cone)
t.set_volume(phantom)
projections, vol_reco = test_tomo(t)

t.set_projections(projections)

# %% test pb
t = tomo.setup(det_shape, angles)
projections, vol_reco = test_tomo(t)


# %% test supersampling fdk
t = tomo.setup(det_shape, angles, cone=cone)
projections = t.project(phantom)
vol_reco = t.reconstruct()
show_image(vol_reco, name="normal")

voxel_size = 0.5
t_fine = tomo.setup(det_shape, angles, cone=cone, voxel_size=voxel_size)
vol_reco_fine = t_fine.reconstruct(projections)
show_image(vol_reco_fine, scale=(voxel_size,)*3, name="fine")


# %% test supersampling pb
t = tomo.setup(det_shape, angles)
projections = t.project(phantom)
vol_reco = t.reconstruct()
show_image(vol_reco, name="normal")

voxel_size = 0.5
t_fine = tomo.setup(det_shape, angles, voxel_size=voxel_size)
vol_reco_fine = t_fine.reconstruct(projections)
show_image(vol_reco_fine, scale=(voxel_size,)*3, name="fine")


# %% test fanflat
i_slice = det_shape[0] // 2
# i_slice = int(det_shape[0] * 0.3)
show_image(phantom[i_slice])
t = tomo.setup(det_shape[1], angles, cone=cone)
projections, vol_reco = test_tomo(t, phantom=phantom[i_slice])


# %% test parallel2d
i_slice = det_shape[0] // 2
show_image(phantom[i_slice])
t = tomo.setup(det_shape[1], angles)
projections, vol_reco = test_tomo(t, phantom=phantom[i_slice])


# %% test 2d stacks
def test_tomo_stack(t, phantom=phantom):
    projections = t.project_stack(phantom)
    show_image(projections)

    vol_reco = t.reconstruct_stack(projections)
    show_image(vol_reco)

    return projections, vol_reco

# %% test pb
t = tomo.setup(det_shape[1], angles)
projections, vol_reco = test_tomo_stack(t)

# %% fanflat
t = tomo.setup(det_shape[1], angles, cone=cone)
projections, vol_reco = test_tomo_stack(t)

# %% test 2d sirt
i_slice = det_shape[0] // 2
show_image(phantom[i_slice])
t = tomo.setup(det_shape[1], angles, algorithm="SIRT_CUDA")
projections = t.project(phantom[i_slice])
t.set_volume(np.zeros_like(phantom[i_slice]))
for i in range(5):
    vol_reco = t.reconstruct(iterations=5)
    show_image(vol_reco)

# %% test 3d sirt
t = tomo.setup(det_shape, angles, algorithm="SIRT3D_CUDA")
projections = t.project(phantom)
t.set_volume(np.zeros_like(phantom))
for i in range(5):
    vol_reco = t.reconstruct(iterations=5)
    show_image(vol_reco)

# %% test tomoalignment
t = tomo.setup(det_shape, angles, cone=cone)
t.apply_shift(4 * np.linspace(-1, 1, numangles))
t.roll_rotaxis(1 * np.linspace(-1, 1, numangles))
projections = t.project(phantom)
show_image(projections)
geo_clean = t.p_geometry

t = tomo.setup(det_shape, angles, cone=cone)
vol_reco_dist = t.reconstruct(projections)
show_image(vol_reco_dist)
t.p_geometry = geo_clean
vol_reco_clean = t.reconstruct(projections)
show_image(vol_reco_clean)

# %%
