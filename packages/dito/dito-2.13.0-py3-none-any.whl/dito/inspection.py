"""
This submodule provides functionality for inspecting images and their properties.
"""

import collections
import hashlib
import io
import pathlib

import cv2
import numpy as np

import dito.core
import dito.utils


__all__ = [
    "info",
    "pinfo",
    "hist",
    "phist",
    "hash_readable",
    "hash_bytes",
    "hash_file",
    "hash_image",
    "hash_image_any_row_order",
    "hash_image_any_col_order",
    "hash_image_any_pixel_order",
]


def info(image, extended=False, minimal=False):
    """
    Returns an ordered dictionary containing info about the given image.

    For default parameters, the following statistics are returned:
    - array shape
    - array dtype
    - mean value
    - standard deviation of all values
    - minimum value
    - maximum value
    - SHA-512 hash value (first eight hex digits)

    Parameters
    ----------
    image : numpy.ndarray
        The image to extract info from.
    extended : bool, optional
        If True, additional statistics are computed (size, 1st quartile, median, 3rd quartile).
    minimal : bool, optional
        If True, only shape and dtype are computed.

    Returns
    -------
    collections.OrderedDict
        An ordered dictionary containing the computed image statistics.
    """

    if not isinstance(image, np.ndarray):
        raise ValueError("Argument 'image' must be of type 'numpy.ndimage', but is '{}'".format(type(image)))

    if extended and minimal:
        raise ValueError("Both arguments 'extended' and 'minimal' must not be true at the same time")

    result = collections.OrderedDict()
    if extended:
        result["size"] = dito.utils.human_bytes(byte_count=image.size * image.itemsize)

    # these are the only stats shown when 'minimal' is true
    result["shape"] = image.shape
    result["dtype"] = image.dtype

    if not minimal:
        result["mean"] = np.mean(image) if image.size > 0 else np.nan
        result["std"] = np.std(image) if image.size > 0 else np.nan
        result["min"] = np.min(image) if image.size > 0 else np.nan
    if extended:
        result["1st quartile"] = np.percentile(image, 25.0) if image.size > 0 else np.nan
        result["median"] = np.median(image) if image.size > 0 else np.nan
        result["3rd quartile"] = np.percentile(image, 75.0) if image.size > 0 else np.nan
    if not minimal:
        result["max"] = np.max(image) if image.size > 0 else np.nan
        result["hash"] = hash_image(image=image, cutoff_position=8, return_hex=True)
    return result


def pinfo(*args, extended_=False, minimal_=False, file_=None, **kwargs):
    """
    Prints info about the given images.

    Parameters
    ----------
    *args : tuple of numpy.ndarray or str or pathlib.Path
        The images to extract info from. Can be either loaded images or filenames (as strings or pathlib.Path objects).
    extended_ : bool, optional
        If True, additional statistics are computed. See `info`.
    minimal_ : bool, optional
        If True, only shape and dtype are computed. See `info`.
    file_ : str or file-like object, optional
        If given, the output is written to this file instead of stdout.
    **kwargs : dict
        Additional images to extract info from. The keys are used as names for the images in the output.

    Returns
    -------
    None
        This function only writes output to stdout (or the given file).
    """

    # merge args and kwargs into one dictionary
    all_kwargs = collections.OrderedDict()
    for (n_image, image) in enumerate(args):
        if isinstance(image, str) or isinstance(image, pathlib.Path):
            # if `image` is a filename (str or pathlib.Path), use the filename as key
            all_kwargs[str(image)] = image
        else:
            # otherwise, use the position of the image in the argument list as key
            all_kwargs["{}".format(n_image)] = image
    all_kwargs.update(kwargs)

    header = None
    rows = []
    for (image_name, image) in all_kwargs.items():
        if isinstance(image, str):
            # `image` is a filename -> load it first
            image = dito.io.load(filename=image)
        image_info = info(image=image, extended=extended_, minimal=minimal_)
        if header is None:
            header = ("Image",) + tuple(image_info.keys())
            rows.append(header)
        row = [image_name] + list(image_info.values())

        # round float values to keep the table columns from exploding
        for (n_col, col) in enumerate(row):
            if isinstance(col, float):
                row[n_col] = dito.utils.adaptive_round(number=col, digit_count=8)

        rows.append(row)

    dito.utils.ptable(rows=rows, ftable_kwargs={"first_row_is_header": True}, print_kwargs={"file": file_})


def hist(image, bin_count=256):
    """
    Return the histogram of the specified image.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which the histogram should be computed. Only numpy.uint8 type is supported.
    bin_count : int, optional
        The number of bins to use for the histogram. Default is 256.

    Returns
    -------
    numpy.ndarray
        The computed histogram. The output has the shape (`bin_count`,) and is of type numpy.float32.

    Raises
    ------
    ValueError
        If the given image is not a valid grayscale or color image.

    Example
    -------
    >>> hist(np.array([[0]], dtype=np.uint8), bin_count=16).shape
    (16,)

    >>> hist(np.array([[0, 0, 0, 1, 1, 2, 3, 4, 5]], dtype=np.uint8))[:8]
    array([3., 2., 1., 1., 1., 1., 0., 0.], dtype=float32)
    """
    
    # determine which channels to use
    if dito.core.is_gray(image):
        channels = [0]
    elif dito.core.is_color(image):
        channels = [0, 1, 2]
    else:
        raise ValueError("The given image must be a valid gray scale or color image")
    
    # accumulate histogram over all channels
    hist_ = sum(cv2.calcHist([image], [channel], mask=None, histSize=[bin_count], ranges=(0, 256)) for channel in channels)
    hist_ = np.squeeze(hist_)
    
    return hist_
    

def phist(image, bin_count=25, height=8, bar_symbol="#", background_symbol=" ", col_sep="."):
    """
    Print the histogram of the given image.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which the histogram should be computed and printed.
    bin_count : int, optional
        The number of bins to use for the histogram. Default is 25. See `hist`.
    height : int, optional
        The height of the printed histogram in number of rows. Default is 8.
    bar_symbol : str, optional
        The symbol to use for filled histogram bars. Default is "#".
    background_symbol : str, optional
        The symbol to use for empty histogram bars. Default is " ".
    col_sep : str, optional
        The separator to use between columns of the histogram. Default is ".".
    """
    
    h = hist(image=image, bin_count=bin_count)
    h = h / np.max(h)
    
    print("^")
    for n_row in range(height):
        col_strs = []
        for n_bin in range(bin_count):
            if h[n_bin] > (1.0 - (n_row + 1) / height):
                col_str = bar_symbol
            else:
                col_str = background_symbol
            col_strs.append(col_str)
        print("|" + col_sep.join(col_strs))
    print("+" + "-" * ((bin_count - 1) * (1 + len(col_sep)) + 1) + ">")


#
# hashing
#


def hash_readable(readable, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of a readable object.

    Parameters
    ----------
    readable : file-like object
        The readable object for which to calculate the hash value. It must implement the `read` method which returns a
        `bytes` object.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The hash value of the readable object.
    """

    hash_ = hashlib.sha512()

    while True:
        chunk = readable.read(hash_.block_size)
        if len(chunk) > 0:
            hash_.update(chunk)
        else:
            break

    # get hash value
    if return_hex:
        digest = hash_.hexdigest()
    else:
        digest = hash_.digest()

    # apply cutoff (if it is None, this returns the full string)
    return digest[:cutoff_position]


def hash_bytes(bytes_, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of a `bytes` object.

    Parameters
    ----------
    bytes_ : bytes
        The bytes object for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The hash value of the `bytes` object.
    """
    return hash_readable(readable=io.BytesIO(initial_bytes=bytes_), cutoff_position=cutoff_position, return_hex=return_hex)


def hash_file(path, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of a file.

    Parameters
    ----------
    path : str
        The path to the file for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The hash value of the file.
    """
    with open(path, "rb") as file:
        return hash_readable(readable=file, cutoff_position=cutoff_position, return_hex=return_hex)


def hash_image(image, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of an image.

    In addition to the image's raw byte data, the image shape and dtype also influence the hash value.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The hash value of the image.
    """
    bytes_ = io.BytesIO(initial_bytes=image.tobytes())
    bytes_.write(str(image.shape).encode("utf-8"))
    bytes_.write(str(image.dtype).encode("utf-8"))
    bytes_.seek(0)
    return hash_readable(bytes_, cutoff_position=cutoff_position, return_hex=return_hex)


def hash_image_any_row_order(image, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of an image which is invariant regarding the order of the rows.

    Even if the hash value is invariant to the order of the rows: the column order, image shape, and image dtype do
    influence the hash value.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The row-order-invariant hash value of the image.
    """
    row_hashes = [hash_image(image=image[n_row, ...], cutoff_position=None, return_hex=False) for n_row in range(image.shape[0])]
    row_hashes = sorted(row_hashes)
    return hash_bytes(bytes_=b"".join(row_hashes), cutoff_position=cutoff_position, return_hex=return_hex)


def hash_image_any_col_order(image, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of an image which is invariant regarding the order of the columns.

    Even if the hash value is invariant to the order of the columns: the row order, image shape, and image dtype do
    influence the hash value.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The column-order-invariant hash value of the image.
    """
    col_hashes = [hash_image(image=image[:, n_col, ...], cutoff_position=None, return_hex=False) for n_col in range(image.shape[1])]
    col_hashes = sorted(col_hashes)
    return hash_bytes(bytes_=b"".join(col_hashes), cutoff_position=cutoff_position, return_hex=return_hex)


def hash_image_any_pixel_order(image, cutoff_position=None, return_hex=True):
    """
    Calculate the SHA-512 hash value of an image which is invariant regarding the order of the pixels.

    Even if the hash value is invariant to the order of the pixels: the image shape and dtype do influence the hash
    value.

    Parameters
    ----------
    image : numpy.ndarray
        The image for which to calculate the hash value.
    cutoff_position : int or None, optional
        The position at which to cut off the hash value. If `None`, the full hash value is returned. Default is `None`.
    return_hex : bool, optional
        If `True`, the hash value is returned as a hexadecimal string. If `False`, it is returned as bytes. Default is
        `True`.

    Returns
    -------
    str or bytes
        The row-order-invariant hash value of the image.
    """
    image_sorted = image.copy()
    image_sorted.shape = (-1,)
    image_sorted = np.sort(image_sorted)
    image_sorted.shape = image.shape
    return hash_image(image=image_sorted, cutoff_position=cutoff_position, return_hex=return_hex)
