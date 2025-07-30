# %%
import numpy as np
import matplotlib.pyplot as plt
from hotopy.datasets import balls
# import napari
# v = napari.Viewer()
# show_image = v.add_image

# %% default tomo phantom
det_shape = height, width = (120, 128)
phantom = balls((height, width, width))
# show_image(phantom)
plt.imshow(phantom.sum(0))

# %% 2d random locations
# shape = (5, 128)
shape = (120, 128)
num_balls = 10
np.random.seed(112)
centers = shape * np.random.random((num_balls, len(shape)))
plt.imshow(balls(shape, centers=centers))

# %% 3d random locations and sizes
shape = (120, 128, 128)
num_balls = 10
np.random.seed(123)
centers = shape * np.random.random((num_balls, len(shape)))
radii = shape[0] / 10 * np.random.random(num_balls)
densities = 1 / radii
phantom = balls(shape, centers, radii, densities)
# show_image(phantom)
plt.imshow(phantom.sum(0))
