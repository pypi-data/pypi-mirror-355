# %%
import numpy as np
from hotopy.image import affine_transform2D, register_images, register_rot
from skimage.registration import phase_cross_correlation

# %% setup viewer
import napari
v = napari.Viewer()
show_image = v.add_image

# import matplotlib.pyplot as plt
# def show_image(image):
#     plt.figure()
#     plt.imshow(image)
#     plt.colorbar()

# show_image = lambda img: None

# %%
from hotopy.datasets import spider
image = spider()["holograms"] + 0.01

# from hotopy.datasets import dicty
# image = as_tensor(dicty())

image -= image.min()
image /= image.mean()
image += 0.01
images = image[:-5]

# show_image(image)

# %% test shift registration
# transfom image
def noise():
    # return 0
    return 1 * np.random.random(image.shape)
shift = np.array((11, 53.563))
reference = image + noise()
transformed = affine_transform2D(image, -shift) + noise()
show_image(reference)
show_image(transformed)

# test registration
registered_shift = register_images(
    reference, transformed, upsample_factor=100
)[0]

print(f"{shift = }")
print(f"{registered_shift = }")
assert np.abs(shift - registered_shift).max() < 1

# direct phase_cross_correlation result
registered_shift = phase_cross_correlation(
    reference, transformed, normalization='phase', upsample_factor=100
)[0]

print(f"{shift = }")
print(f"{registered_shift = }")
assert np.abs(shift - registered_shift).max() < 1


# %% no relevant speedup seen from doing fft in torch
# from torch import as_tensor
# from torch.fft import fft2
# def register_shift(
#     im_ref,
#     im_mov,
#     upsample_factor: float = 10,
#     device=None,
# ) -> tuple:
#     """only registers rotations around the image center"""
#     images = torch.stack((as_tensor(im_ref), as_tensor(im_mov))).to(device=device)

#     images = fft2(images).cpu().numpy()
#     shift = phase_cross_correlation(
#         images[0],
#         images[1],
#         space="fourier",
#         normalization="phase",
#         upsample_factor=upsample_factor,
#     )[0]
#     return shift

# registered_shift = -register_shift(
#     reference, transformed, upsample_factor=100
# )

# print(f"{shift = }")
# print(f"{registered_shift = }")
# assert np.abs(shift - registered_shift).max() < 1

# # %%timeit
# registered_shift = -phase_cross_correlation(
#     reference, transformed, normalization='phase', upsample_factor=100
# )[0]
# # %%
# # %%timeit
# registered_shift = -register_shift(
#     reference, transformed, upsample_factor=100
# )
# # %%
# # %%timeit
# registered_shift = -register_shift(
#     reference, transformed, upsample_factor=100, device='cuda'
# )

# %% test rotation registration
rot =  5.764

registered_rot = register_rot(
    image,
    affine_transform2D(image, rotate=-rot),
    upsample_factor = 20
)

print(f"{rot = }")
print(f"{registered_rot = }")
assert np.abs(rot - registered_rot).max() < 0.1


# %% register shift + rotation
shift, rot = np.array((-9.645, 12.56345)), 5.764
# shift, rot = np.array((0, 0)), 5.764

registered_shift, registered_rot = register_images(
    image,
    affine_transform2D(image, shift=-shift, rotate=-rot),
    upsample_factor = 20,
    mode = "shift_rot"
)

print(f"{rot = }")
print(f"{registered_rot = }")
assert np.abs(rot - registered_rot).max() < 1

print(f"{shift = }")
print(f"{registered_shift = }")
assert np.abs(shift - registered_shift).max() < 1
