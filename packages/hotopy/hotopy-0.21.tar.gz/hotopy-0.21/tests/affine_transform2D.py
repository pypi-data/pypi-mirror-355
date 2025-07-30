# %%
import numpy as np
import torch
from hotopy.image import affine_transform2D

# %% setup viewer
import napari
v = napari.Viewer()
show_image = v.add_image

# import matplotlib.pyplot as plt
# show_image = plt.imshow

# show_image = lambda img: None

# %%
from hotopy.datasets import spider
image = spider()["holograms"] + 0.01

# from hotopy.datasets import dicty
# image = as_tensor(dicty())

show_image(image)

# %% shift
shifted = affine_transform2D(image, (0, 500))
show_image(shifted)

# %% stack
shifted = affine_transform2D(np.stack((image,)*4), (0, 500))
show_image(shifted)

# %% rotate
rot = affine_transform2D(image, rotate=15)
show_image(rot)

# %% magnify
mag = affine_transform2D(image, magnify=0.8)
show_image(mag)

# %% combine
combined = affine_transform2D(
    image,
    (60, 20),  # shift
    10.2,  # rot
    0.7,  # magnify
    )
show_image(combined)

# % inverse
back = affine_transform2D(
    combined,
    (60, 20),  # shift
    10.2,  # rot
    0.7,  # magnify
    inv = True
    )

error = (back - image) / image
show_image(error)

if torch.any(error.abs() > 0.2):
    raise ValueError("The errors of the inverse are quiet large")

# %% complex

rot = affine_transform2D(image * (1 + 1j), rotate=15)
show_image(rot.abs())

rot = affine_transform2D(image, rotate=15)
show_image(rot.abs())
