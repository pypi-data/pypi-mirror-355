# %%
from hotopy.image import MedianFilter2d

import numpy as np
imshape = (2048+1, 2048)

np.random.seed(1234)
rng = np.random.default_rng(seed=1234)
image = rng.random(imshape).astype(np.float32)

kernel_size = (5, 5)

# %%
median_filter = MedianFilter2d(kernel_size)
filtered_torch = median_filter(image).cpu().numpy()

# %%
from hotopy.utils import Padder
import scipy

pad = Padder(image.shape, np.array(kernel_size) // 2, mode="reflect")
filtered_scipy = pad.inv(scipy.signal.medfilt2d(pad(image), kernel_size))

# %%
np.testing.assert_allclose(filtered_torch, filtered_scipy)
