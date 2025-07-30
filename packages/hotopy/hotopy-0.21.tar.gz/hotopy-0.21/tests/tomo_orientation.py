# %%
# remarks
# shape of projections:
#     (nangles, height, width)
#     (nangles, width)

# shape of volumes:
#     (width, width)
#     (height, width, width)

import numpy as np
import matplotlib.pyplot as plt
from hotopy import tomo
import astra
astra.astra.set_gpu_index(1)

import napari
v = napari.Viewer()
show_image = v.add_image

# phantom
from hotopy.datasets import balls
det_shape = height, width = (120, 128)
phantom = balls((height, width, width))
show_image(phantom)

# %% geometry
numangles = int(1.5 * width)
angles = np.linspace(0, 2 * np.pi, numangles + 1)[:-1]
z01, z02, px = 99, 100, 1
cone = (z01, z02, px)

i_slice = height // 2

# %%
def verify(vol_data, cone=cone):
    t = tomo.setup(vol_data.shape[:-1], angles, cone=cone)
    
    # t.apply_shift(np.linspace(0, 100, numangles))
    # t.apply_shift(np.linspace(0, 100, numangles), move="sample")

    # 3d only
    # t.apply_shift(np.stack(2 * (np.linspace(0, 100, numangles),)).T)
    # t.apply_shift(np.stack(2 * (np.linspace(0, 100, numangles),)).T, move="sample")
    # t.roll_rotaxis(np.linspace(0, 5, numangles))
    # t.pitch_rotaxis(np.linspace(0, 5, numangles))

    projections = t.project(vol_data)
    show_image(projections.squeeze())

# full volume
verify(phantom)
verify(phantom, cone=None)

# single slice
# verify(phantom[i_slice])
# verify(phantom[i_slice], cone=None)

# %%
# below is the "pure" astra code needed to reproduce the projections
# (which is helpful to figure out, that 2d and 3d sinograms are only compatible,
# when flipping the first volume dimension in 2d)
#

# %% determine raw astra geometry
# fanflat
from hotopy.tomo._astra import _transform_geo_pars
sino_pad = 0
voxel_size = 1

vol_data = phantom[i_slice]
show_image(vol_data)

nx = np.atleast_1d(det_shape)[-1]
ncol = nx
m, z01_eff, z12_eff = (par / voxel_size for par in _transform_geo_pars(*cone))
p_geometry = astra.create_proj_geom("fanflat", m, ncol, -angles, z01_eff, z12_eff)
v_geometry = astra.create_vol_geom(nx, nx)

proj_id = astra.data2d.create("-sino", p_geometry)
vol_id = astra.data2d.create("-vol", v_geometry, data=np.flip(vol_data, 0))  # same sinogram as in 3d
# vol_id = astra.data2d.create("-vol", v_geometry, data=vol_data)  # different sinogram than 3d

alg_conf = dict(
    type = "FP_CUDA",
    ProjectionDataId = proj_id,
    VolumeDataId = vol_id,
)
alg_id = astra.algorithm.create(alg_conf)
astra.algorithm.run(alg_id)
projections = astra.data2d.get(proj_id)
show_image(projections)

astra.data2d.delete(proj_id)
astra.data2d.delete(vol_id)
astra.algorithm.delete(alg_id)

# %% determine raw astra geometry
# cone
from hotopy.tomo._astra import _transform_geo_pars, algorithm_config
sino_pad = 0
voxel_size = 1

vol_data = phantom[i_slice][None]
# vol_data = phantom

show_image(vol_data.squeeze())

det_shape = vol_data.shape[:2]
nrow = det_shape[-2]
nslices = nrow
nx = np.atleast_1d(det_shape)[-1]
ncol = nx
m, z01_eff, z12_eff = (par / voxel_size for par in _transform_geo_pars(*cone))
p_geometry = astra.create_proj_geom("cone", m, m, nrow, ncol, -angles, z01_eff, z12_eff)
# alg_cfg = algorithm_config("FDK_CUDA")
v_geometry = astra.create_vol_geom(nx, nx, nslices)

proj_id = astra.data3d.create("-sino", p_geometry)
vol_id = astra.data3d.create("-vol", v_geometry, data=vol_data)
# vol_id = astra.data3d.create("-vol", v_geometry, data=np.flip(vol_data, 1))

alg_conf = dict(
    type = "FP3D_CUDA",
    ProjectionDataId = proj_id,
    VolumeDataId = vol_id,
)
alg_id = astra.algorithm.create(alg_conf)
astra.algorithm.run(alg_id)
projections = astra.data3d.get(proj_id)
show_image(projections.squeeze())

astra.data3d.delete(proj_id)
astra.data3d.delete(vol_id)
astra.algorithm.delete(alg_id)
