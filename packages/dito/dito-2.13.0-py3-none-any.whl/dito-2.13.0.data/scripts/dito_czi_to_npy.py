#!python

import argparse
import glob
import os.path
import sys

import dito


def get_args():
    parser = argparse.ArgumentParser(description="Convert CZI (Carl Zeiss Image) files to NumPy arrays.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--debug", action="store_true", help="If set, show full stack trace for errors.")
    parser.add_argument("-s", "--keep-singleton-dimensions", action="store_true", help="If set, keep dimensions in the final NumPy array even if their size is 1.")
    parser.add_argument("-a", "--keep-all-dimensions", action="store_true", help="If set, the final NumPy array will have all dimensions that are possible for CZI files.")
    parser.add_argument("image_filenames", type=str, nargs="+", help="Input image filenames. Patterns are allowed.")
    args = parser.parse_args()
    return args


def main(args):
    if args.image_filenames is None:
        raise ValueError("No image filenames specified")

    filenames = []
    for image_filename in args.image_filenames:
        filenames += glob.glob(os.path.expanduser(image_filename))
    filenames = sorted(filenames)

    file_count = len(filenames)
    if file_count == 0:
        raise FileNotFoundError("Found no images with the filenames(s) {}".format(args.image_filenames))

    for filename_czi in filenames:
        # check if extension is '.czi'
        filename_split = os.path.splitext(filename_czi)
        if filename_split[1].lower() != ".czi":
            raise RuntimeError("File '{}' does not end on '.czi'".format(filename_czi))

        # load image from CZI
        image = dito.load(
            filename_czi,
            czi_kwargs={
                "keep_singleton_dimensions": args.keep_singleton_dimensions,
                "keep_all_dimensions": args.keep_all_dimensions,
            },
        )

        # save image as NumPy array
        filename_npy = filename_split[0] + ".npy"
        dito.save(filename_npy, image)


if __name__ == "__main__":
    args_ = get_args()
    try:
        main(args=args_)
    except Exception as e:
        if args_.debug:
            raise
        else:
            print("ERROR: {} ({})".format(e, type(e).__name__))
            sys.exit(1)
