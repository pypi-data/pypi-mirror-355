from hotopy.image import remove_outliers
import numpy as np
from tqdm import tqdm

# shape = (20, 2000, 2000)
shape = (10, 20, 20)
num_hot_pixels = int(np.prod(shape) / 1e2)
kwargs = {
    "kernel_size": 5,
}

print(f"{shape = }")
print(f"{num_hot_pixels = }")
print(f"{kwargs = }")

rng = np.random.default_rng(seed=1234)
images = rng.normal(1, 1, shape).astype(np.float32)
hot_pixels = np.array([rng.integers(s, size=num_hot_pixels) for s in shape])
images[(*hot_pixels,)] += 20 * rng.random(num_hot_pixels)

print("median (torch)")
filtered = np.array([remove_outliers(img, imfilter="median", **kwargs) for img in tqdm(images)])

print("median (torch), cuda")
filtered = np.array([remove_outliers(img, imfilter="median", device='cuda', **kwargs) for img in tqdm(images)])

# import napari
# v = napari.view_image(images);
# v.add_image(filtered)
