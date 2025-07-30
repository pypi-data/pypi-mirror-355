"""
io - Input output

TODO(Paul): document when I know, how to document modules
"""

import numpy as np
import re

mat_type_conversion = {"single": np.float32, "double": np.float64}


def read_matlab_raw(filename, output="array"):
    """Read a raw file created by the holotomotoolbox.

    Load the contents of a .raw file created by the saveraw function in the
    holotomotoolbox (matlab) into a numpy.ndarray (output=='array'). As in
    matlab, the returned array is stored in Fortran (column-major) order.
    If output is set to 'memmap', a memory map of the data located in the file
    is returned instead.

    Parameters
    ----------
    filename : string, or any object that can be converted into a path-representing string, for example pathlib.Path objects.
        filename, which has to include the format data type and shape
        (see example).
    output : {'array', 'mmap'}
        whether to return a copy of the data in a np.ndarray
        or a read-only memory map

    Returns
    -------
    data : numpy.ndarray (default) or numpy.memmap
        data

    Notes
    -----
    The data type and array size are deduced from the filename. This function
    exists only for compatibility with data from the holotomotoolbox.

    Examples
    --------
    >>> fname = 'reconstructedSlices_type=single_size=1260x120x1050.raw'
    >>> data = read_matlab_raw(fname)
    """
    filename = str(filename)  # for support of pathlib objects.

    # extract type and size from filename
    match = re.search(r".*_type=(\w+)_size=((\d+)(x\d+)+).raw", filename)

    try:
        dtype = mat_type_conversion[match.group(1)]
    except KeyError as e:
        raise NotImplementedError(
            f"type {match.group(1)} could not be converted to a numpy type"
        ) from e

    shape = tuple(int(i) for i in match.group(2).split("x"))

    if output == "array":
        return np.fromfile(filename, dtype).reshape(shape, order="F")
    elif output == "memmap":
        return np.memmap(filename, dtype, mode="r", shape=shape, order="F")
    else:
        raise ValueError(f"'{output}' is not a valid output type. Use 'array' or 'memmap'")


def save_matlab_raw(data, prefix):
    """Save an array in raw format as the holotomotoolbox does.

    Saves the contents of the array `data` in (column-major) raw format, like
    the holotomotoolbox (matlab) does. Appends the suffix "type=<>_size=<>.raw".

    Parameters
    ----------
    data : numpy.ndarray
        data
    prefix : string, or any object that can be converted into a path-representing string, for example pathlib.Path objects.
        prefix of the created files name. Can also include the path.

    Returns
    -------
    filename : string
        full name of the created file

    Notes
    -----
    This function exists only for compatibility with data from the holotomotoolbox.

    Examples
    --------
    >>> import numpy as np
    >>> data = np.random.random((10, 11, 12), dtype=np.float32)
    >>> save_matlab_raw(data, "tmp/mydata")
    saved file: tmp/mydata_type=single_size=10x11x12.raw
    """
    prefix = str(prefix)  # support pathlib paths
    if prefix.endswith(".raw"):
        prefix = prefix[-4:]
    # determine filename
    for mat_type, np_type in mat_type_conversion.items():
        if np.issubdtype(data.dtype, np_type):
            break  # mat_type is found
    else:  # for-else!
        raise NotImplementedError(f"dtype {data.dtype} not supported")
    size_str = "x".join((str(s) for s in data.shape))
    filename = f"{prefix}_type={mat_type}_size={size_str}.raw"

    np.asfortranarray(data.T).tofile(filename)
    return filename
