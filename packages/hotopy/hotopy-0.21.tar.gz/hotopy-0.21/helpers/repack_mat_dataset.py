import numpy as np
from scipy.io import loadmat
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input .mat file path")
    parser.add_argument("output", help="Output .npz file path")
    parser.add_argument(
        "--no-hash",
        help="Do not compute hash of new .npz file.",
        default=False,
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        "--ndim-swap",
        help="Swaps last axis and first axis of array with three or more dims.",
        default=True,
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        "--squeeze",
        help="Calls squeeze onto arrays.",
        default=True,
        action=argparse.BooleanOptionalAction
    )
    args = parser.parse_args()

    try:
        cnt = loadmat(args.input)
    except FileNotFoundError as e:
        print(f"Can not find input file {args.input!s}")
        exit(1)

    # filter non-data keys, like __header__
    data = {}
    for key in cnt.keys():
        if not key.startswith("__"):
            val = cnt[key]

            if args.ndim_swap and isinstance(val, np.ndarray):
                if val.ndim > 2:
                    val = np.moveaxis(val, -1, 0)

            if args.squeeze and isinstance(val, np.ndarray):
                val = np.squeeze(val)

            data[key] = val

    print(f"attempting to save contents {data.keys()!r}")

    target = str(args.output)
    np.savez_compressed(target, **data)

    # calculate hash for pooch registry
    if not args.no_hash:
        try:
            import pooch
        except ModuleNotFoundError as e:
            print("pooch module not found. Please install pooch or disable hash calculation with --no-hash option.")
        else:
            filehash = pooch.file_hash(target)
            print(f"{target}:\t{filehash}")
