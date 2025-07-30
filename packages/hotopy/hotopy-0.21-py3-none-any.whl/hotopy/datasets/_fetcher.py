import numpy as np
import pooch
import importlib.resources  # requires python>=3.7


class _DataFetcher:
    def __init__(self):
        self.storage = pooch.create(
            path=pooch.os_cache("hotopy/datasets"),
            base_url="https://gitlab.gwdg.de/irp/",
            registry=None,
            env="HOTOPY_DATA_DIR",
        )

        # find registry
        self._registry_fp = registry_fp = importlib.resources.files(__package__).joinpath(
            "registry.txt"
        )
        self.storage.load_registry(registry_fp)

    def __call__(self, *args, **kwargs):
        defaults = {"processor": _process_npz}
        kwargs = {**defaults, **kwargs}
        return self.storage.fetch(*args, **kwargs)


def _process_npz(fname, *args):
    return np.load(fname)


def _decompress_npz(fname, *args):
    decompressor = pooch.processors.Decompress()
    fd_inflated = decompressor(fname, *args)
    return np.load(fd_inflated)


fetcher = _DataFetcher()
