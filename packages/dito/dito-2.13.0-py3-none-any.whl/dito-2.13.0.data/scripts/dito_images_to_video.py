#!python

import argparse
import glob
import os.path
import sys

import dito


def get_args():
    parser = argparse.ArgumentParser(description="Convert a sequence of images into a video.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-d", "--debug", action="store_true", help="If set, show full stack trace for errors.")
    parser.add_argument("-o", "--output-filename", type=str, default="out.avi", help="Filename of the output video.")
    parser.add_argument("-c", "--codec", type=str, default="MJPG", help="The FourCC code of the video codec to use.")
    parser.add_argument("-f", "--fps", type=float, default=30.0, help="Frames per second the output video should have.")
    parser.add_argument("-g", "--gray", action="store_true", help="If set, create a gray scale video. Otherwise, a color video will be created.")
    parser.add_argument("-i", "--input-filenames", type=str, nargs="+", default=["*.png"], help="Input image filenames. Patterns are allowed.")
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    filenames = []
    for input_filename in args.input_filenames:
        filenames += glob.glob(os.path.expanduser(input_filename))
    filenames = sorted(filenames)
    file_count = len(filenames)
    if file_count == 0:
        raise FileNotFoundError("Found no images with the filenames(s) {}".format(args.input_filenames))
    print("Found {} image(s)".format(file_count))

    print("Saving video '{}'...".format(args.output_filename))
    with dito.VideoSaver(filename=args.output_filename, codec=args.codec, fps=args.fps, color=not args.gray) as saver:
        for (n_file, filename) in enumerate(filenames):
            print("[{}/{}]  {}".format(n_file + 1, file_count, filename))
            image = dito.load(filename=filename)
            saver.append(image)
    saver.print_summary()


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
