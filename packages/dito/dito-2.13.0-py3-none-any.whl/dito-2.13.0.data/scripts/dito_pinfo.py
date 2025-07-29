#!python

import argparse
import glob
import os.path
import sys

import dito


def get_args():
    parser = argparse.ArgumentParser(description="Print basic information for the images with the given filenames.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--debug", action="store_true", help="If set, show full stack trace for errors.")
    parser.add_argument("-e", "--extended", action="store_true", help="If set, show extended information (e.g., quartiles).")
    parser.add_argument("-m", "--minimal", action="store_true", help="If set, show minimal information (shape and dtype only).")
    parser.add_argument("image_filenames", type=str, nargs="+", help="Input image filenames. Patterns are allowed.")
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    if args.image_filenames is None:
        raise ValueError("No image filenames specified")

    filenames = []
    for image_filename in args.image_filenames:
        filenames += glob.glob(os.path.expanduser(image_filename))
    filenames = sorted(filenames)
    file_count = len(filenames)
    if file_count == 0:
        raise FileNotFoundError("Found no images with the filenames(s) {}".format(args.image_filenames))

    dito.pinfo(*filenames, extended_=args.extended, minimal_=args.minimal)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        args = get_args()
        if args.debug:
            raise
        else:
            print("ERROR: {} ({})".format(e, type(e).__name__))
            sys.exit(1)
