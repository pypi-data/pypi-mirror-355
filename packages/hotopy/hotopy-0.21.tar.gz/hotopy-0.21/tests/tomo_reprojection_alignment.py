# %%
import numpy as np
import matplotlib.pyplot as plt
from hotopy import tomo
import astra
from hotopy.datasets import balls
from tqdm import tqdm
astra.astra.set_gpu_index(1)

import napari
v = napari.Viewer()

show_image = v.add_image

# phantom
scale_system = 1
det_shape = height, width = np.array((120, 128)) * scale_system
phantom = balls((height, width, width))
show_image(phantom)

# %% acquisition
numangles = int(width * np.pi)
z01, z02, px = 99, 100, 0.5 / scale_system
angles = np.linspace(0, 2*np.pi, numangles+1)[:-1]

rng = np.random.default_rng(seed=1234)
shift_horz = 3 * rng.normal(size=numangles) + np.linspace(-2, 2, numangles) + 3
shift_vert = 1.5 * rng.normal(size=numangles) + 5 * np.linspace(-1, 1, numangles)

# remove total translation
s = np.sin(angles)
s /= np.linalg.norm(s)
c = np.cos(angles)
c /= np.linalg.norm(c)
shift_horz -= np.dot(s, shift_horz) * s + np.dot(c, shift_horz) * c  # horizontal
shift_vert -= shift_vert.mean()

shift = np.stack((shift_horz, shift_vert)).T

# roll_deg = 3 * rng.normal(size=numangles)
roll_deg = 0

t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
t.roll_rotaxis(roll_deg)
# move_what = "sample"
move_what = "detector"
t.apply_shift(shift, move=move_what)
# t.apply_shift(shift, move="detector")
projections = t.project(phantom)
show_image(projections)

# %% ideal reconstruction
t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
t.roll_rotaxis(roll_deg)
t.apply_shift(shift, move=move_what)
reco_ideal = t.reconstruct(projections)
show_image(reco_ideal)

# # %% direct reconstruction
# t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
# reco_direct = t.reconstruct(projections)
# show_image(reco_direct)

# %% reprojection alignment
from hotopy.image import GaussianBandpass, AveragePool2d

from importlib import reload
reload(tomo)

binning = 1
t = tomo.setup(det_shape // binning, angles, cone=(z01, z02, px * binning), sino_pad="corner")
# t = tomo.setup(det_shape // binning, angles, cone=(z01, z02, px * binning), sino_pad=0)
do_bin = AveragePool2d(binning)
# t.set_projections(do_bin(projections))
# t.set_projections(GaussianBandpass(t.det_shape, 1, 2)(do_bin(projections)).numpy())
# t.set_projections(GaussianBandpass(t.det_shape, 1, 2)(do_bin(projections)).numpy())
rep_al = tomo.ReprojectionAlignment(t, do_bin(projections), move=move_what)
rep_al.vol_constraint = tomo.Constraints(vmin=0)
found_shift = rep_al(tol=0.1, max_iter=200, upsample=20)
all_shifts = rep_al.solver.monitor.trajectory

vol_reco = t.reconstruct()
show_image(vol_reco, scale=(binning,)*3)

# result_shifts[:, :, :2] *= binning
# t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
# t.apply_shift(result_shifts[-1])
# reco_corrected = t.reconstruct(projections)
# show_image(reco_corrected)

plt.semilogy(rep_al.convergence, label="conv_norm")
plt.axhline(rep_al.solver.tol, ls='--', label="tolerance")
plt.xlabel("iteration")
plt.legend()

# %%
plt.imshow(vol_reco[vol_reco.shape[0]//2])

# %%
from hotopy.tomo._reprojection_alignment import _default_convergence_norm
norms = list(map(_default_convergence_norm, np.diff(all_shifts, axis=0)))
plt.semilogy(range(len(norms)), norms)
plt.semilogy(range(len(rep_al.convergence)), rep_al.convergence)

# %%
# # %%
plt.figure()
plt.plot(shift, label="ground truth")
plt.plot(found_shift, ".",label="determined shifts")
plt.legend()


plt.figure()
for i in range(2):
    plt.scatter(shift[:, i], found_shift[:, i])
min_shift = min(shift.min(), found_shift.min())
max_shift = max(shift.max(), found_shift.max())
plt.plot((min_shift, max_shift), (min_shift, max_shift), "r--")
plt.xlabel("true shift")
plt.ylabel("determined shift")

# %%
# plt.plot(result_shifts[:, :, 0])
plt.plot((all_shifts[:, :, 1] - all_shifts[-1,:,1]))
# plt.ylim((-1, 1))

# %% plot shift updates
direction = 0
plt.plot(np.diff(all_shifts[:,:,direction], 1, axis=0), '-x');
# plt.xlim((3, None))
plt.ylim((-1, 1))
plt.ylabel("shift update")
plt.xlabel("iteration")
plt.grid()
plt.title("updates to the individual projections")
# %%
from hotopy.image import GaussianBandpass

t = tomo.setup(det_shape, angles, cone=(z01, z02, px))
reco_dirty = t.reconstruct(projections)
reprojections = t.project()

reference_length = max(t.det_shape)
bands = reference_length / 5000, reference_length / 2
print(bands)
proj_filter = GaussianBandpass(t.det_shape, *bands)


projections_f = proj_filter(projections)
reprojections_f = proj_filter(reprojections)

show_image(projections_f)
show_image(reprojections_f)
