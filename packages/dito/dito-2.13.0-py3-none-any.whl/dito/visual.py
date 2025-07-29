"""
This submodule provides functionality related to visualizing images.
"""

import collections
import math
import os.path
import pathlib
import warnings

import cv2
import numpy as np

import dito.core
import dito.data
import dito.exceptions
import dito.io
import dito.utils


DEFAULT_WINDOW_NAME = "dito.show"


#
# color-related
#


def random_color(min_hue=0, max_hue=180, min_saturation=128, max_saturation=255, min_value=128, max_value=255):
    """
    Generate a random BGR color with HSV values within given ranges.

    Parameters
    ----------
    min_hue : int, optional
        The minimum hue value. Must be between 0 and 180 (inclusive). Default is 0.
    max_hue : int, optional
        The maximum hue value. Must be between 0 and 180 (inclusive). Default is 180.
    min_saturation : int, optional
        The minimum saturation value. Must be between 0 and 255 (inclusive). Default is 128.
    max_saturation : int, optional
        The maximum saturation value. Must be between 0 and 255 (inclusive). Default is 255.
    min_value : int, optional
        The minimum value. Must be between 0 and 255 (inclusive). Default is 128.
    max_value : int, optional
        The maximum value. Must be between 0 and 255 (inclusive). Default is 255.

    Returns
    -------
    tuple of int
        A tuple of 3 integers, containing the BGR values of the generated color.

    Raises
    ------
    ValueError
        If `min_hue` is less than 0 or greater than 180.
    """
    # check arguments
    if not (0 <= min_hue <= 180):
        raise ValueError("Argument 'min_hue' must be a value between 0 and 180 (inclusive), but is '{}'".format(min_hue))

    # wrap-around hue
    while max_hue < min_hue:
        max_hue += 180

    random_hsv = (
        np.random.randint(low=min_hue, high=max_hue + 1) % 180,
        np.random.randint(low=min_saturation, high=max_saturation + 1),
        np.random.randint(low=min_value, high=max_value + 1),
    )
    return dito.core.hsv_to_bgr(image_or_color=random_hsv)


def max_distant_color(color):
    """
    Return the maximally distant uint8 color for a given uint8 color.

    The maximally distant color is obtained by setting each channel value that
    is less or equal to 127 in the input `color` to 255, and by setting each channel
    value that is greater than 127 to 0.

    Parameters
    ----------
    color : tuple of int
        The uint8 color for which to find the maximally distant color. It must
        be a tuple of integers, each in the range [0, 255].

    Returns
    -------
    tuple of int
        The maximally distant uint8 color.

    Examples
    --------
    >>> max_distant_color((100, 200, 50))
    (255, 0, 255)
    >>> max_distant_color((128, 127, 255))
    (0, 255, 0)
    >>> max_distant_color((10,))
    (255,)
    """
    return tuple(255 if item <= 127 else 0 for item in color)


def get_colormap(name):
    """
    Return the colormap of the specified name.

    The colormap is a `uint8` NumPy array of size `(256, 1, 3)`. This is the
    OpenCV format for colormaps.

    Parameters
    ----------
    name : str
        The case-insensitive name of the colormap to retrieve. This can be either
        the name of a builtin OpenCV colormap (e.g., "jet" for `cv2.COLORMAP_JET`)
        or a non-OpenCV colormap present in dito's resources folder.

    Returns
    -------
    numpy.ndarray
        A `uint8` NumPy array of size `(256, 1, 3)` representing the colormap.

    Raises
    ------
    ValueError
        If `name` is not a recognized colormap name.
    """
    
    # source 1: non-OpenCV colormaps
    data_key = "colormap:{}".format(name.lower())
    if data_key in dito.data.RESOURCES_FILENAMES.keys():
        return dito.io.load(filename=dito.data.RESOURCES_FILENAMES[data_key])
    
    # source 2: OpenCV colormaps
    full_cv2_name = "COLORMAP_{}".format(name.upper())
    if hasattr(cv2, full_cv2_name):
        return cv2.applyColorMap(src=dito.data.yslope(width=1), colormap=getattr(cv2, full_cv2_name))
    
    # no match
    raise ValueError("Unknown colormap '{}'".format(name))


def is_colormap(colormap):
    """
    Return `True` if `colormap` is an OpenCV-compatible colormap.

    Parameters
    ----------
    colormap : numpy.ndarray
        The colormap to be checked. Must be a `uint8` array of shape `(256, 1, 3)`, i.e.
        a color image of size `1x256`.

    Returns
    -------
    bool
        `True` if `colormap` is an OpenCV-compatible colormap, `False` otherwise.
    """
    if not dito.core.is_image(image=colormap):
        return False
    if colormap.dtype != np.uint8:
        return False
    if colormap.shape != (256, 1, 3):
        return False
    return True


def create_colormap(colors):
    """
    Create a colormap by interpolating between a given set of anchor colors.

    Parameters
    ----------
    colors : dict or tuple
        The anchor colors used for the colormap. If a dictionary, it should have
        integer keys between 0 and 255, specifying the source intensity, and
        3-tuples as corresponding values, specifying the BGR colors. If a tuple
        of 3-tuples, they are spread evenly over the whole source intensity range.

    Returns
    -------
    colormap : ndarray
        The generated colormap as a `uint8` NumPy array of size `(256, 1, 3)`.

    Raises
    ------
    TypeError
        If `colors` is not a dictionary or can not be transformed into one.
    ValueError
        If `colors` is empty or does not satisfy the requirements specified
        above.
    """

    # transform color list into color dict
    if isinstance(colors, collections.abc.Sequence):
        color_count = len(colors)
        colors = {math.floor(255.0 * n_color / (color_count - 1)): color for (n_color, color) in enumerate(colors)}

    # check argument 'colors'
    if not isinstance(colors, collections.abc.Mapping):
        raise TypeError("Argument 'colors' must be a dictionary, but is of type '{}'".format(type(colors)))
    if len(colors) == 0:
        raise ValueError("Argument 'colors' must be a non-empty dictionary, but is empty")
    if not all(isinstance(key, int) and 0 <= key <= 255 for key in colors.keys()):
        raise ValueError("Argument 'colors' must have integer keys, all between 0 and 255")
    if not all(isinstance(value, collections.abc.Sequence) and (len(value) == 3) and (isinstance(item, int) and 0 <= item <= 255 for item in value) for value in colors.values()):
        raise ValueError("Argument 'colors' must have 3-tuple values with integer items between 0 and 255")

    # create colormap
    sorted_keys = sorted(colors.keys())
    sorted_values = tuple(colors[key] for key in sorted_keys)
    colormap = np.zeros(shape=(256, 1, 3), dtype=np.uint8)
    for n_channel in range(3):
        sorted_channel_values = tuple(value[n_channel] for value in sorted_values)
        for n_color in range(256):
            colormap[n_color, 0, n_channel] = np.interp(x=n_color, xp=sorted_keys, fp=sorted_channel_values)

    return colormap


def colorize(image, colormap):
    """
    Colorize the input `image` using the specified `colormap`.

    Parameters
    ----------
    image : numpy.ndarray
        The input grayscale image to be colorized. Must have dtype `numpy.uint8`.
    colormap : str or numpy.ndarray
        The colormap to use for colorizing the image. If `colormap` is a string,
        it is interpreted as the name of a colormap and a colormap is loaded with
        the specified name (see `get_colormap`). If `colormap` is a NumPy array,
        it is assumed to be a colormap as a uint8 NumPy array of shape `(256, 1, 3)`.

    Returns
    -------
    numpy.ndarray
        The colorized image, as a NumPy array of the same shape as the input
        `image` and of dtype `numpy.uint8`.

    Raises
    ------
    TypeError
        If the `colormap` argument is not a valid colormap or colormap name.

    Notes
    -----
    The `cv2.applyColorMap` function only works for OpenCV versions >= 3.3.0.
    Therefore, this function uses `cv2.LUT` to apply the colormap to the image.
    """
    if isinstance(colormap, str):
        # get colormap by name
        colormap = get_colormap(name=colormap)
    elif is_colormap(colormap=colormap):
        # argument is already a colormap
        pass
    else:
        raise TypeError("Argument `colormap` must either be a string (the colormap name) or a valid colormap.")

    # cv2.applyColorMap(src=image, userColor=colormap) only works for OpenCV>=3.3.0
    # (below that version, only internal OpenCV colormaps are supported)
    # thus, we use cv2.LUT
    image = dito.core.as_color(image=dito.core.as_gray(image=image))
    return cv2.LUT(src=image, lut=colormap)


def gamma(image, exponent):
    """
    Apply the gamma transform with the given `exponent` on the given `image`.

    Parameters
    ----------
    image : numpy.ndarray
        The input image.
    exponent : float
        The exponent to use for the gamma transformation.

    Returns
    -------
    numpy.ndarray
        The transformed image. Has the same shape and dtype as the input `image`.
    """
    if image.dtype == np.uint8:
        lut = np.round(255.0 * np.linspace(start=0.0, stop=1.0, num=256)**exponent).astype(np.uint8)
        lut.shape = (256, 1, 1)
        result = cv2.LUT(src=image, lut=lut)
    else:
        dtype = image.dtype
        image_float = dito.convert(image=image, dtype=np.float32)
        image_float = image_float**exponent
        result = dito.convert(image=image_float, dtype=dtype)

    # make sure that the output shape is identical to the input shape
    # (cv2.LUT removes the channel axis if it had size one)
    result.shape = image.shape

    return result


#
# image combination
#


def stack(images, padding=0, background_color=0, dtype=None, gray=None):
    """
    Arrange multiple images side-by-side into one image.

    Parameters
    ----------
    images : tuple of ndarrays or tuple of tuples of ndarrays
        Vector of images (in which case the images are stacked horizontally) or a
        vector of vectors of images, defining rows and columns.

    padding : int, optional (default=0)
        Amount of padding to add between the images in pixels.

    background_color : int, optional (default=0)
        Background color of the output image. Currently, only single integers
        are supported. This will be fixed in a later release.

    dtype : data-type, optional (default=None)
        Data type of the resulting image. If None, the data type is chosen to
        be the common data type of the input images.

    gray : bool, optional (default=None)
        If `True`/`False`, output is converted to grayscale/color. If `None`,
        the output color mode is chosen based on the input images.

    Returns
    -------
    numpy.ndarray
        The stacked image.
    """

    # check argument `images`
    if isinstance(images, (tuple, list)) and (len(images) > 0) and isinstance(images[0], np.ndarray):
        # `images` is a vector of images
        rows = [images]
    elif isinstance(images, (tuple, list)) and (len(images) > 0) and isinstance(images[0], (tuple, list)) and (len(images[0]) > 0) and isinstance(images[0][0], np.ndarray):
        # `images` is a vector of vectors of images
        rows = images
    else:
        raise ValueError("Invalid argument 'images' - must be vector of images or vector of vectors of images")

    # find common data type and color mode
    if dtype is None:
        dtype = dito.core.dtype_common((image.dtype for row in rows for image in row))
    if gray is None:
        gray = all(dito.core.is_gray(image=image) for row in rows for image in row)

    # float64 causes problems in some OpenCV routines (e.g., cvtColor)
    if dtype == np.float64:
        dtype = np.float32

    # step 1/2: construct stacked image for each row
    row_images = []
    width = 0
    for (n_row, row) in enumerate(rows):
        # determine row height
        row_height = 0
        for image in row:
            row_height = max(row_height, image.shape[0])
        if n_row == 0:
            row_height += 2 * padding
        else:
            row_height += padding

        # construct image
        row_image = None
        for (n_col, image) in enumerate(row):
            # convert individual image to target data type and color mode
            image = dito.core.convert(image=image, dtype=dtype)
            if gray:
                image = dito.core.as_gray(image=image)
            else:
                image = dito.core.as_color(image=image)

            # add padding
            pad_width = [[padding if n_row == 0 else 0, padding], [padding if n_col == 0 else 0, padding]]
            if not gray:
                pad_width.append([0, 0])
            image = np.pad(array=image, pad_width=pad_width, mode="constant", constant_values=background_color)

            # ensure that image has the height of the row
            gap = row_height - image.shape[0]
            if gap > 0:
                if gray:
                    image_fill = np.zeros(shape=(gap, image.shape[1]), dtype=dtype) + background_color
                else:
                    image_fill = np.zeros(shape=(gap, image.shape[1], 3), dtype=dtype) + background_color
                image = np.vstack(tup=(image, image_fill))

            # add to current row image
            if row_image is None:
                row_image = image
            else:
                row_image = np.hstack(tup=(row_image, image))

        # update max width
        width = max(width, row_image.shape[1])
        row_images.append(row_image)

    # step 2/2: construct stacked image from the row images
    stacked_image = None
    for row_image in row_images:
        # ensure that the row image has the width of the final image
        gap = width - row_image.shape[1]
        if gap > 0:
            if gray:
                image_fill = np.zeros(shape=(row_image.shape[0], gap), dtype=dtype) + background_color
            else:
                image_fill = np.zeros(shape=(row_image.shape[0], gap, 3), dtype=dtype) + background_color
            row_image = np.hstack(tup=(row_image, image_fill))

        # add to final image
        if stacked_image is None:
            stacked_image = row_image
        else:
            stacked_image = np.vstack(tup=(stacked_image, row_image))

    return stacked_image


def astack(images, aspect=1.77, padding=0, **stack_kwargs):
    """
    Arranges the given images side-by-side into an image with an aspect ratio as close as possible to `aspect`.

    Parameters
    ----------
    images : tuple of ndarray
        A list of images to stack.
    aspect : float, optional
        The desired aspect ratio. Default is 1.77 (= 16:9).
    padding : int, optional
        The amount of padding to add between images. Default is 0.
    **stack_kwargs :
        Additional keyword arguments passed to `stack`.

    Returns
    -------
    numpy.ndarray
        The stacked image.
    """

    # find the optimal image count per row
    image_count = len(images)
    best_image_count_per_row = 1
    best_error = float("inf")
    for image_count_per_row in range(1, image_count + 1):
        total_height = 0
        total_width = 0
        n_image_row = 0
        row_height = 0
        row_width = 0
        for (n_image, image) in enumerate(images):
            row_height = max(row_height, image.shape[0] + padding)
            row_width += image.shape[1] + padding
            if ((n_image_row + 1) == image_count_per_row) or ((n_image + 1) == image_count):
                total_height += row_height
                total_width = max(total_width, row_width)
                n_image_row = 0
                row_height = 0
                row_width = 0
            else:
                n_image_row += 1
        total_height += padding
        total_width += padding

        error = abs(aspect - (total_width / total_height))
        if error < best_error:
            best_image_count_per_row = image_count_per_row
            best_error = error

    # construct 2d list of images
    rows = []
    row = []
    for (n_image, image) in enumerate(images):
        row.append(image)
        if (len(row) == best_image_count_per_row) or ((n_image + 1) == image_count):
            rows.append(row)
            row = []

    return stack(images=rows, padding=padding, **stack_kwargs)


def stack_channels(image, mode="row", **kwargs):
    """
    Arrange the channels of the given image side-by-side into one image.

    Parameters
    ----------
    image : ndarray
        The input image to stack the channels of.
    mode : str, optional
        The mode of stacking to use. Possible values are "row", "col", and "auto".
        If `"row"`, stack the channels horizontally. If `"col"`, stack the channels vertically.
        If `"auto"`, stack the channels in the mode with the aspect ratio closest to 16:9.
        Defaults to `"row"`.
    **kwargs : dict, optional
        Additional keyword arguments to pass to the `stack` or `astack` function.

    Returns
    -------
    ndarray
        The stacked image with the channels of the input image.

    Raises
    ------
    ValueError
        If the input image has invalid shape or the mode is not valid.
    """

    # check the image shape
    if len(image.shape) < 3:
        return image
    if len(image.shape) > 3:
        raise ValueError("Invalid image shape: {}".format(image.shape))

    channel_count = image.shape[2]
    channel_images = [image[:, :, n_channel] for n_channel in range(channel_count)]
    if mode == "row":
        # row-wise stacking
        return stack(images=[channel_images], **kwargs)
    elif mode == "col":
        # col-wise stacking
        return stack(images=[[channel_image] for channel_image in channel_images], **kwargs)
    elif mode == "auto":
        return astack(images=channel_images)
    else:
        raise ValueError("Invalid mode: '{}'".format(mode))


def insert(target_image, source_image, position=(0, 0), anchor="lt", source_mask=None):
    """
    Insert `source_image` into `target_image` at the specified `position`.

    Parameters
    ----------
    target_image : ndarray
        The target image into which `source_image` will be inserted. Will be
        copied. Therefore, the original `target_image` will remain unchanged.
    source_image : ndarray
        The source image that will be inserted into `target_image`.
    position : tuple of float or int, optional
        The position where `source_image` will be inserted, specified as a 2-tuple
        `(x, y)`. If the position is specified as integers, it is interpreted as
        an absolute position in pixels. If the position is specified as floats,
        it is interpreted as a relative position as a fraction of the width and
        height of `target_image`. Default is `(0, 0)`.
    anchor : str, optional
        The anchor point used to align `source_image` with the `position`. The
        anchor is a 2-character string of the form `[lcr][tcb]`. The first character
        defines the horizontal anchor (*l*eft, *c*enter, or *r*ight), and the second
        character defines the vertical anchor (*t*op, *c*enter, or *b*ottom).
        Default is `"lt"`, i.e., align `source_image` with its top-left corner at
        the `position`.
    source_mask : ndarray or float, optional
        Determines the opacity of `source_image`. If a float is provided, it is
        interpreted as the opacity of the source image. If it is a mask, it must
        have the same shape as `source_image` and its values must be in the range
        [0, 1]. If `source_mask` is `None` (default), `source_image` is fully opaque.

    Returns
    -------
    ndarray
        A copy of `target_image` with `source_image` inserted.

    Raises
    ------
    ValueError
        If `target_image` or `source_image` are not valid images or have different
        data types.
        If `source_mask` is not None and has invalid values or an invalid data type.
        If `position` or `anchor` are not valid.

    Notes
    -----
    If `source_image` is a grayscale image and `target_image` is a color image, the
    former is converted to color before insertion.

    If the region where `source_image` is inserted extends beyond the bounds of
    `target_image`, the overflowing part is truncated.
    """

    # check argument 'position'
    if not (isinstance(position, (tuple, list)) and (len(position) == 2) and isinstance(position[0], (int, float)) and isinstance(position[1], (int, float))):
        raise ValueError("Argument 'position' must be a 2-tuple (or list) of int (absolute) or float (relative) values")

    # check if source and target are images
    if not dito.core.is_image(image=target_image):
        raise ValueError("Argument 'target_image' must be valid image")
    if not dito.core.is_image(image=source_image):
        raise ValueError("Argument 'source_image' must be valid image")

    # check if source and target have the same dtype
    if target_image.dtype != source_image.dtype:
        raise ValueError("Arguments 'target_image' and 'source_image' must have the same dtypes (but have dtypes '{}' and '{}')".format(target_image.dtype, source_image.dtype))

    # make sure that source_mask is either None or a NumPy array
    if source_mask is None:
        pass
    elif isinstance(source_mask, float):
        source_mask = np.zeros(shape=source_image.shape[:2], dtype=np.float32) + source_mask
    elif isinstance(source_mask, np.ndarray):
        source_mask = source_mask.copy()
    else:
        raise ValueError("Argument 'source_mask' must be (i) `None` (meaning full opacity), (ii) a float (same opacity for all pixels), or (iii) a float image (individual opacity for each pixel)")

    # check source mask
    if source_mask is not None:
        if not np.issubdtype(source_mask.dtype, np.floating):
            raise ValueError("Source mask must be a float image")
        if (not np.all(0.0 <= source_mask)) or (not np.all(source_mask <= 1.0)):
            raise ValueError("Source mask must have values between 0.0 and 1.0")

    # make sure source and target have a channel axis and that its value is identical
    target_image = target_image.copy()
    source_image = source_image.copy()
    if dito.core.is_gray(image=target_image):
        if not dito.core.is_gray(image=source_image):
            raise ValueError("Target image is a grayscale image, but source image is a color image")
        target_image.shape += (1,)
        source_image.shape += (1,)
    else:
        if dito.core.is_gray(image=source_image):
            source_image = dito.core.as_color(image=source_image)
    channel_count = target_image.shape[2]

    # determine base offset based on argument 'position'
    offset = np.zeros(shape=(2,), dtype=np.float32)
    for (n_dim, dim_position) in enumerate(position):
        if isinstance(dim_position, int):
            # int -> absolute position
            offset[n_dim] = float(dim_position)
        else:
            # float -> relative position
            offset[n_dim] = dim_position * target_image.shape[1 - n_dim]

    # adjust offset based on the specified anchor type
    if not (isinstance(anchor, str) and (len(anchor) == 2) and (anchor[0] in ("l", "c", "r")) and (anchor[1] in ("t", "c", "b"))):
        raise ValueError("Argument 'anchor' must be a string of length two (pattern: '[lcr][tcb]') , but is '{}'".format(anchor))
    (anchor_h, anchor_v) = anchor
    if anchor_h == "l":
        pass
    elif anchor_h == "c":
        offset[0] -= source_image.shape[1] * 0.5
    elif anchor_h == "r":
        offset[0] -= source_image.shape[1]
    if anchor_v == "t":
        pass
    elif anchor_v == "c":
        offset[1] -= source_image.shape[0] * 0.5
    elif anchor_v == "b":
        offset[1] -= source_image.shape[0]

    # convert offset to integers
    offset = dito.core.tir(*offset)

    # extract target region
    target_indices = (
        slice(max(0, offset[1]), max(0, min(target_image.shape[0], offset[1] + source_image.shape[0]))),
        slice(max(0, offset[0]), max(0, min(target_image.shape[1], offset[0] + source_image.shape[1]))),
    )
    target_region = target_image[target_indices + (Ellipsis,)]

    # cut out the matching part of the rendered image
    source_offset = (max(0, -offset[0]), max(0, -offset[1]))
    source_indices = (
        slice(source_offset[1], source_offset[1] + target_region.shape[0]),
        slice(source_offset[0], source_offset[0] + target_region.shape[1]),
    )
    source_region = source_image[source_indices + (Ellipsis,)]

    # insert rendered image into the target image
    if source_mask is None:
        target_image[target_indices + (Ellipsis,)] = source_region
    else:
        for n_channel in range(channel_count):
            target_image[target_indices + (n_channel,)] = (source_mask[source_indices] * source_region[:, :, n_channel] + (1.0 - source_mask[source_indices]) * target_region[:, :, n_channel]).astype(target_image.dtype)

    # remove channel axis for gray scale images
    if (len(target_image.shape) == 3) and (target_image.shape[2] == 1):
        target_image = target_image[:, :, 0]

    return target_image


def overlay(target_image, source_image, source_mask=None):
    """
    Overlay the source image onto the target image using the specified mask.

    This function is equivalent to using `insert` with arguments `position=(0, 0)`
    and `anchor="lt"`. Thus, it is best suited for equally-sized source and target images.

    Parameters
    ----------
    target_image : numpy.ndarray
        The target image
    source_image : numpy.ndarray
        The source image
    source_mask : numpy.ndarray or float, optional
        Determines the opacity of `source_image`. If a float is provided, it is
        interpreted as the opacity of the source image. If it is a mask, it must
        have the same shape as `source_image` and its values must be in the range
        [0, 1]. If `source_mask` is `None` (default), `source_image` is fully opaque.

    Returns
    -------
    numpy.ndarray
        A copy of `target_image` with `source_image` inserted.
    """
    return insert(target_image=target_image, source_image=source_image, source_mask=source_mask)


def overlay_constant(target_image, source_color, source_mask):
    """
    Overlay a constant color image onto a target image using a source mask.

    The function creates a constant image with the specified color and blends it with the target image using the
    specified source mask. The resulting image has the same shape and dtype as the target image.

    Parameters
    ----------
    target_image : numpy.ndarray
        The target image
    source_color : tuple
        The color of the constant image as a tuple of values for each channel. For `np.uint8` images, the values range
        between 0 and 255, while for floats the range is between 0.0 and 1.0 (for more details, see
        `dito.core.dtype_range`).
    source_mask : numpy.ndarray or float
        Determines the opacity of `source_color`. If a float is provided, it is
        interpreted as the opacity of the source color. If it is a mask, it must
        have the same shape as `target_image` and its values must be in the range
        [0, 1].

    Returns
    -------
    numpy.ndarray
        The blended image with the same shape and dtype as the target image.
    """
    return insert(
        target_image=target_image,
        source_image=dito.data.constant_image(size=dito.core.size(target_image), color=source_color, dtype=target_image.dtype),
        source_mask=source_mask,
    )


#
# text
#


class Font():
    """
    Base class for font handling.

    It provides ANSI escape codes (special strings that can be inserted into the
    text) to format text style and color. See https://en.wikipedia.org/wiki/ANSI_escape_code.

    These escape codes work on supported terminals as well as when rendering the
    text into an image using the functionality within this library.

    Attributes
    ----------
    RESET : str
        ANSI escape code that resets all styles and colors.
    
    STYLE_REGULAR : str
        ANSI escape code that sets the text style to regular (non-bold).
    STYLE_BOLD : str
        ANSI escape code that sets the text style to bold.
    
    REVERSE_ON : str
        ANSI escape code that turns on reverse mode (switching foreground and background colors).
    REVERSE_OFF : str
        ANSI escape code that turns off reverse mode (switching foreground and background colors).
    
    FOREGROUND_DEFAULT : str
        ANSI escape code that sets the foreground color to the default color.
    BACKGROUND_DEFAULT : str
        ANSI escape code that sets the background color to the default color.
    
    FOREGROUND_BLACK : str
        ANSI escape code that sets the foreground color to black.
    FOREGROUND_RED : str
        ANSI escape code that sets the foreground color to red.
    FOREGROUND_GREEN : str
        ANSI escape code that sets the foreground color to green.
    FOREGROUND_YELLOW : str
        ANSI escape code that sets the foreground color to yellow.
    FOREGROUND_BLUE : str
        ANSI escape code that sets the foreground color to blue.
    FOREGROUND_MAGENTA : str
        ANSI escape code that sets the foreground color to magenta.
    FOREGROUND_CYAN : str
        ANSI escape code that sets the foreground color to cyan.
    FOREGROUND_WHITE : str
        ANSI escape code that sets the foreground color to white.
    
    BACKGROUND_BLACK : str
        ANSI escape code that sets the background color to black.
    BACKGROUND_RED : str
        ANSI escape code that sets the background color to red.
    BACKGROUND_GREEN : str
        ANSI escape code that sets the background color to green.
    BACKGROUND_YELLOW : str
        ANSI escape code that sets the background color to yellow.
    BACKGROUND_BLUE : str
        ANSI escape code that sets the background color to blue.
    BACKGROUND_MAGENTA : str
        ANSI escape code that sets the background color to magenta.
    BACKGROUND_CYAN : str
        ANSI escape code that sets the background color to cyan.
    BACKGROUND_WHITE : str
        ANSI escape code that sets the background color to white.
    
    FOREGROUND_BRIGHT_BLACK : str
        ANSI escape code that sets the foreground color to bright black.
    FOREGROUND_BRIGHT_RED : str
        ANSI escape code that sets the foreground color to bright red.
    FOREGROUND_BRIGHT_GREEN : str
        ANSI escape code that sets the foreground color to bright green.
    FOREGROUND_BRIGHT_YELLOW : str
        ANSI escape code that sets the foreground color to bright yellow.
    FOREGROUND_BRIGHT_BLUE : str
        ANSI escape code that sets the foreground color to bright blue.
    FOREGROUND_BRIGHT_MAGENTA : str
        ANSI escape code that sets the foreground color to bright magenta.
    FOREGROUND_BRIGHT_CYAN : str
        ANSI escape code that sets the foreground color to bright cyan.
    FOREGROUND_BRIGHT_WHITE : str
        ANSI escape code that sets the foreground color to bright white.
    
    BACKGROUND_BRIGHT_BLACK : str
        ANSI escape code that sets the background color to bright black.
    BACKGROUND_BRIGHT_RED : str
        ANSI escape code that sets the background color to bright red.
    BACKGROUND_BRIGHT_GREEN : str
        ANSI escape code that sets the background color to bright green.
    BACKGROUND_BRIGHT_YELLOW : str
        ANSI escape code that sets the background color to bright yellow.
    BACKGROUND_BRIGHT_BLUE : str
        ANSI escape code that sets the background color to bright blue.
    BACKGROUND_BRIGHT_MAGENTA : str
        ANSI escape code that sets the background color to bright magenta.
    BACKGROUND_BRIGHT_CYAN : str
        ANSI escape code that sets the background color to bright cyan.
    BACKGROUND_BRIGHT_WHITE : str
        ANSI escape code that sets the background color to bright white.
    """

    RESET = "\033[0m"

    STYLE_REGULAR = "\033[22m"
    STYLE_BOLD = "\033[1m"

    REVERSE_ON = "\033[7m"
    REVERSE_OFF = "\033[27m"

    FOREGROUND_DEFAULT = "\033[39m"
    BACKGROUND_DEFAULT = "\033[49m"

    FOREGROUND_BLACK   = "\033[30m"
    FOREGROUND_RED     = "\033[31m"
    FOREGROUND_GREEN   = "\033[32m"
    FOREGROUND_YELLOW  = "\033[33m"
    FOREGROUND_BLUE    = "\033[34m"
    FOREGROUND_MAGENTA = "\033[35m"
    FOREGROUND_CYAN    = "\033[36m"
    FOREGROUND_WHITE   = "\033[37m"

    BACKGROUND_BLACK   = "\033[40m"
    BACKGROUND_RED     = "\033[41m"
    BACKGROUND_GREEN   = "\033[42m"
    BACKGROUND_YELLOW  = "\033[43m"
    BACKGROUND_BLUE    = "\033[44m"
    BACKGROUND_MAGENTA = "\033[45m"
    BACKGROUND_CYAN    = "\033[46m"
    BACKGROUND_WHITE   = "\033[47m"

    FOREGROUND_BRIGHT_BLACK   = "\033[90m"
    FOREGROUND_BRIGHT_RED     = "\033[91m"
    FOREGROUND_BRIGHT_GREEN   = "\033[92m"
    FOREGROUND_BRIGHT_YELLOW  = "\033[93m"
    FOREGROUND_BRIGHT_BLUE    = "\033[94m"
    FOREGROUND_BRIGHT_MAGENTA = "\033[95m"
    FOREGROUND_BRIGHT_CYAN    = "\033[96m"
    FOREGROUND_BRIGHT_WHITE   = "\033[97m"

    BACKGROUND_BRIGHT_BLACK   = "\033[100m"
    BACKGROUND_BRIGHT_RED     = "\033[101m"
    BACKGROUND_BRIGHT_GREEN   = "\033[102m"
    BACKGROUND_BRIGHT_YELLOW  = "\033[103m"
    BACKGROUND_BRIGHT_BLUE    = "\033[104m"
    BACKGROUND_BRIGHT_MAGENTA = "\033[105m"
    BACKGROUND_BRIGHT_CYAN    = "\033[106m"
    BACKGROUND_BRIGHT_WHITE   = "\033[107m"

    @staticmethod
    def _COLOR_BGR(b, g, r, foreground=True):
        """
        Generate an ANSI escape code for the specified BGR text color.

        Parameters
        ----------
        b : int
            The blue channel of the color. Must be an integer between 0 and 255.
        g : int
            The green channel of the color. Must be an integer between 0 and 255.
        r : int
            The red channel of the color. Must be an integer between 0 and 255.
        foreground : bool, optional
            If `True` (the default), the code is for a foreground color, otherwise it is for a background color.

        Returns
        -------
        str
            The generated ANSI escape code.
        """
        for value in (b, g, r):
            if not (isinstance(value, int) and (0 <= value <= 255)):
                raise ValueError("BGR values must be integers in the range [0, 255]")
        return "\033[{};2;{};{};{}m".format(38 if foreground else 48, r, g, b)

    @classmethod
    def FOREGROUND_BGR(cls, b, g, r):
        """
        Generate an ANSI escape code for the specified BGR text foreground color.

        Parameters
        ----------
        b : int
            The blue channel of the color. Must be an integer between 0 and 255.
        g : int
            The green channel of the color. Must be an integer between 0 and 255.
        r : int
            The red channel of the color. Must be an integer between 0 and 255.

        Returns
        -------
        str
            The generated ANSI escape code.
        """
        return cls._COLOR_BGR(b=b, g=g, r=r, foreground=True)

    @classmethod
    def BACKGROUND_BGR(cls, b, g, r):
        """
        Generate an ANSI escape code for the specified BGR text background color.

        Parameters
        ----------
        b : int
            The blue channel of the color. Must be an integer between 0 and 255.
        g : int
            The green channel of the color. Must be an integer between 0 and 255.
        r : int
            The red channel of the color. Must be an integer between 0 and 255.

        Returns
        -------
        str
            The generated ANSI escape code.
        """
        return cls._COLOR_BGR(b=b, g=g, r=r, foreground=False)


class MonospaceBitmapFont(Font):
    """
    Class for monospace bitmap font handling.

    This class derives from the `Font` class and implements a monospace bitmap font with a fixed character width and
    height. The font is loaded from a file in dito's own monospace bitmap font format ("df2").

    Attributes
    ----------
    filename : str
        Path to the font file in dito's own monospace bitmap font format ("df2").
    char_width : int
        Width of each character in the font.
    char_height : int
        Height of each character in the font.
    char_images : OrderedDict
        Dictionary containing the character images for the font. The keys are the characters themselves and the values
        are sub-dictionaries with keys 'regular' and 'bold', each containing the corresponding image as a NumPy array.
    """

    def __init__(self, filename):
        """
        Initialize a new `MonospaceBitmapFont` object.

        Parameters
        ----------
        filename : str or pathlib.Path
            Path to the font file in dito's own monospace bitmap font format ('df2').
        """
        self.filename = filename
        if isinstance(self.filename, pathlib.Path):
            self.filename = str(self.filename)
        (self.char_width, self.char_height, self.char_images) = self.load_df2(filename=self.filename)

    @classmethod
    def init_from_name(cls, name):
        """
        Instantiate a `MonospaceBitmapFont` object from a given font name.

        This method looks up the filename for the given font name in the `dito.data.RESOURCES_FILENAMES` dictionary and
        returns a new `MonospaceBitmapFont` object initialized with the corresponding filename.

        Parameters
        ----------
        name : str
            Name of the font to be loaded.

        Returns
        -------
        MonospaceBitmapFont
            A new `MonospaceBitmapFont` object initialized with the font file for the given font name.

        Raises
        ------
        KeyError
            If the given font name is unknown.
        """
        key = "font:{}".format(name)
        try:
            filename = dito.data.RESOURCES_FILENAMES[key]
        except KeyError:
            raise KeyError("Unknown font '{}'".format(name))
        return cls(filename=filename)

    @classmethod
    def save_df2(cls, filename, char_images_regular, char_images_bold):
        """
        Save the given character images in dito's own monospace bitmap font format ('df2').

        For a description of the format, see `load_df2`.
        This method is usually only called when adding new fonts to dito.

        Parameters
        ----------
        filename : str or pathlib.Path
            Path to the file in which to save the font data.
        char_images_regular : dict
            Dictionary containing the regular character images. The keys are the characters themselves and the values
            are numpy arrays of shape `(char_height, char_width)`.
        char_images_bold : dict
            Dictionary containing the bold character images. The keys are the characters themselves and the values are
            numpy arrays of shape `(char_height, char_width)`.

        Returns
        -------
        None
        """
        chars = cls.get_supported_chars()
        position_images = []
        for char in chars:
            position_image = (np.round(char_images_regular[char].astype(np.float32) / 17.0).astype(np.uint8) << 4) + np.round(char_images_bold[char].astype(np.float32) / 17.0).astype(np.uint8)
            position_images.append(position_image)
        out_image = stack([position_images])
        dito.io.save(filename=filename, image=out_image)

    @classmethod
    def load_df2(cls, filename):
        """
        Load the font from dito's own monospace bitmap font format ("df2").

        In principle, it is just a PNG image which contains all ISO-8859-1 (= Latin-1) and some other characters
        (see `MonospaceBitmapFont.get_supported_char_codes`) in regular and bold style, stacked horizontally.
        The regular and bold variants of each character are stacked on top of another, each using a depth of four bit.
        This saves quite some space (especially when using a PNG optimizer).

        Parameters
        ----------
        filename : str or pathlib.Path
            The filename of the DF2 file to load.

        Returns
        -------
        Tuple[int, int, Dict[str, Dict[str, numpy.ndarray]]]
            The font's character width and height and a dictionary of numpy arrays, containing the regular and bold
            images of each character.
        """
        chars = cls.get_supported_chars()
        char_count = len(chars)
        chars_per_position = 1

        image = dito.io.load(filename=filename, color=False)
        char_height = image.shape[0]
        char_width = (image.shape[1] * chars_per_position) // char_count

        char_images = collections.OrderedDict()
        for (n_char, char) in enumerate(chars):
            n_position = n_char
            position_image = image[:, (n_position * char_width):((n_position + 1) * char_width)]
            char_images[char] = collections.OrderedDict()
            char_images[char]["regular"] = ((0xF0 & position_image) >> 4) * 17
            char_images[char]["bold"] = (0x0F & position_image) * 17

        return (char_width, char_height, char_images)

    @staticmethod
    def get_supported_char_codes():
        """
        Get the character codes of all characters that are supported by the font.

        Returns
        -------
        tuple of int
            A tuple containing the supported character codes as integers.
        """

        codes = tuple()

        # ISO-8859-1 (= Latin-1)
        codes += tuple(range(32, 127))
        codes += tuple(range(160, 256))

        # Greek alphabet
        codes += tuple(range(913, 930))
        codes += tuple(range(931, 938))
        codes += tuple(range(945, 970))

        return codes

    @classmethod
    def get_supported_chars(cls):
        """
        Get all characters that are supported by the font.

        Returns
        -------
        tuple of str
            A tuple of strings representing all supported Unicode characters.
        """
        codes = cls.get_supported_char_codes()
        return tuple(chr(code) for code in codes)

    def get_char_image(self, char, style="regular"):
        """
        Get the image of a specific character.

        Parameters
        ----------
        char : str
            The character to retrieve the image for.
        style : {"regular", "bold"}, optional
            The font style. If `"regular"`, the normal font style is used. If `"bold"`, the bold font style is used.
            Defaults to `"regular"`.

        Returns
        -------
        numpy.ndarray
            The image of the specified character, as a grayscale image with shape `(self.char_height, self.char_width)`.
            The image data is a 2D array of `numpy.uint8` dtype and values in the range [0, 255].

        Notes
        -----
        If the character is not supported by the font, it will return the image for the character `"?"`.
        """
        return self.char_images.get(char, self.char_images["?"]).get(style, "regular")

    @staticmethod
    def parse_message(raw_message, initial_style, initial_foreground_color, initial_background_color):
        """
        Parses a raw message with escape sequences and returns a dictionary containing the message contents.

        Parameters
        ----------
        raw_message : str
            The raw message with escape sequences to parse.
        initial_style : str
            The initial style of the message.
        initial_foreground_color : tuple of int
            The initial foreground color of the message, as an BGR tuple of integer values in the range [0, 255].
        initial_background_color : tuple of int
            The initial background color of the message, as an BGR tuple of integer values in the range [0, 255].

        Returns
        -------
        dict of str to list of any
            A dictionary containing the parsed message contents, with the following keys:
            - "lines": A list (rows) of lists (columns) of the individual characters.
            - "styles": A list (rows) of lists (columns) of the individual character styles.
            - "foreground_colors": A list (rows) of lists (columns) of the individual character foreground colors as tuples of int.
            - "background_colors": A list (rows) of lists (columns) of the individual character background colors as tuples of int.
        """
        raw_lines = raw_message.split("\n")

        charss = []
        styless = []
        foreground_colorss = []
        background_colorss = []

        current_style = initial_style
        current_foreground_color = initial_foreground_color
        current_background_color = initial_background_color
        current_reverse_state = False

        for raw_line in raw_lines:
            chars = ""
            styles = []
            foreground_colors = []
            background_colors = []

            while len(raw_line) > 0:
                # determine begin and end of leftmost escape pattern
                escape_begin_index = raw_line.find("\033[")
                if escape_begin_index == -1:
                    # no escape pattern was found in the remaining raw line
                    escape_begin_index = len(raw_line)
                    escape_end_index = escape_begin_index
                else:
                    escape_end_index = escape_begin_index + raw_line[escape_begin_index:].find("m") + 1

                # split line into part before the next escape sequence, the escape sequence, the "argument" part of the escape sequence, and the part after the escape sequence
                pre_escape = raw_line[:escape_begin_index]
                escape_sequence = raw_line[escape_begin_index:escape_end_index]
                if escape_sequence != "":
                    escape_codes = tuple(int(code) if code != "" else 0 for code in escape_sequence[2:-1].split(";"))
                else:
                    escape_codes = tuple()
                post_escape = raw_line[escape_end_index:]

                # append text before the escape sequence to the line and update the remaining raw line
                chars += pre_escape
                styles += [current_style] * escape_begin_index
                foreground_colors += [current_foreground_color if (current_reverse_state is False) else current_background_color] * escape_begin_index
                background_colors += [current_background_color if (current_reverse_state is False) else current_foreground_color] * escape_begin_index
                raw_line = post_escape

                # handle escape codes (see https://en.wikipedia.org/wiki/ANSI_escape_code)
                while len(escape_codes) > 0:
                    escape_code = escape_codes[0]
                    escape_codes = escape_codes[1:]

                    if escape_code == 0:
                        # reset
                        current_style = initial_style
                        current_foreground_color = initial_foreground_color
                        current_background_color = initial_background_color
                        current_reverse_state = False

                    elif escape_code == 1:
                        # bold style
                        current_style = "bold"

                    elif escape_code == 7:
                        # turn on reverse mode (foreground and background colors are switched)
                        current_reverse_state = True

                    elif escape_code == 22:
                        # regular (non-bold) style
                        current_style = "regular"

                    elif escape_code == 27:
                        # turn on reverse mode (foreground and background colors are switched)
                        current_reverse_state = False

                    elif (30 <= escape_code <= 37) or (40 <= escape_code <= 47) or (90 <= escape_code <= 97) or (100 <= escape_code <= 107):
                        # set foreground/background color via index

                        first_digits = escape_code // 10
                        last_digit = escape_code % 10

                        # distinguish between "normal" and "bright" colors
                        if first_digits in (3, 4):
                            # normal colors
                            color_lut = {
                                0: (  0,   0,   0), # black
                                1: (  0,   0, 205), # red
                                2: (  0, 205,   0), # green
                                3: (  0, 205, 205), # yellow
                                4: (238,   0,   0), # blue
                                5: (205,   0, 205), # magenta
                                6: (205, 205,   0), # cyan
                                7: (229, 229, 229), # white
                            }
                        else:
                            # bright colors
                            color_lut = {
                                0: (127, 127, 127),  # gray
                                1: (  0,   0, 255),  # bright red
                                2: (  0, 255,   0),  # bright green
                                3: (  0, 255, 255),  # bright yellow
                                4: (255,  92,  92),  # bright blue
                                5: (255,   0, 255),  # bright magenta
                                6: (255, 255,   0),  # bright cyan
                                7: (255, 255, 255),  # bright white
                            }

                        # determine what color to set
                        color = color_lut[last_digit]
                        if first_digits in (3, 9):
                            current_foreground_color = color
                        else:
                            current_background_color = color

                    elif (escape_code in (38, 48)) and (len(escape_codes) >= 4) and (escape_codes[0] == 2):
                        # set foreground/background color via BGR
                        bgr_values = escape_codes[1:4][::-1]
                        escape_codes = escape_codes[4:]

                        if escape_code == 38:
                            # foreground color (bgr)
                            current_foreground_color = bgr_values
                        else:
                            # background color (bgr)
                            current_background_color = bgr_values

                    elif escape_code == 39:
                        # reset foreground color
                        current_foreground_color = initial_foreground_color

                    elif escape_code == 49:
                        # reset background color
                        current_background_color = initial_background_color

                    else:
                        warnings.warn("Escape code '{}' (full escape sequence: {}) is not supported".format(escape_code, bytes(escape_sequence, "utf-8")))

            charss.append(chars)
            styless.append(styles)
            foreground_colorss.append(foreground_colors)
            background_colorss.append(background_colors)

        return {"lines": charss, "styles": styless, "foreground_colors": foreground_colorss, "background_colors": background_colorss}

    def render_into_image(self, target_image, message, position, anchor, style, foreground_color, background_color, background_as_outline, border_color, border, margin, padding, opacity, alignment, scale, rotation, shrink_to_width):
        """
        Render a text message with a specific style and color into an image.

        Parameters
        ----------
        target_image : ndarray
            The image into which the text message is to be rendered. The original `target_image` is not altered.
        message : str
            The text message to be rendered. Can contain ANSI escape codes to set text style and color.
        position : tuple of int
            The position at which the text message is to be placed in the target image. See `insert`.
        anchor : str
            The anchor position of the text message within the target image. See `insert`.
        style : dict
            The initial style of the text message.
        foreground_color : tuple of int
            The initial foreground of the text message.
        background_color : tuple of int or None
            The initial background color of the text message. If `None`, the background is transparent.
        background_as_outline : bool
            If True, the background color will be used as an outline around the text message.
        border_color : tuple of int
            The color of the border around the text message.
        border : int or 4-tuple of int
            The width of the border (top, right, bottom, left) around the text message.
        margin : int or 4-tuple of int
            The margin (top, right, bottom, left) around the text message.
        padding : int or 2-tuple of int
            The padding (vertical, horizontal) for the text message.
        opacity : float or None
            The opacity in the range [0.0, 1.0] of the text message. A value of `None` means full opacity (i.e., no transparency).
        alignment : {"left", "center", "right"}
            The text alignment of each line.
        scale : float or tuple of int or None
            The scaling factor or target size of the text. If `None`, apply no scaling.
        rotation : int or float or None
            The rotation angle (in degrees, counter-clockwise) of the text message. A value of `None` means no rotation.
        shrink_to_width : int or None
            If not `None`, the width of the text will be shrunk to fit the specified width.

        Returns
        -------
        numpy.ndarray
            The resulting image with the rendered text message.
        """

        # parse message (to get the raw text plus style and color information)
        parse_result = self.parse_message(raw_message=message, initial_style=style, initial_foreground_color=foreground_color, initial_background_color=background_color)
        lines = parse_result["lines"]
        styles = parse_result["styles"]
        foreground_colors = parse_result["foreground_colors"]
        background_colors = parse_result["background_colors"]

        # determine max character count per line to get the image size
        line_count = len(lines)
        character_counts = tuple(len(line) for line in lines)
        max_character_count = max(character_counts)

        # check colors
        for (color, none_allowed) in ((foreground_color, False), (background_color, True), (border_color, False)):
            if (not none_allowed) and (not (isinstance(color, (tuple, list)) and (len(color) == 3) and all(isinstance(value, int) for value in color) and all(0 <= value <= 255 for value in color))):
                raise ValueError("Arguments 'color', 'background_color', and 'border_color' must be 3-tuples (8 bit BGR).")

        # check border
        try:
            (border_top, border_right, border_bottom, border_left) = dito.utils.get_validated_tuple(x=border, type_=int, count=4, min_value=0, max_value=None)
        except ValueError:
            raise ValueError("Argument 'border' must be a single non-negative integer (same border for all four sides) or a 4-tuple of non-negative integers (specifying the top, right, bottom, and left border).")

        # check margin
        try:
            (margin_top, margin_right, margin_bottom, margin_left) = dito.utils.get_validated_tuple(x=margin, type_=int, count=4, min_value=0, max_value=None)
        except ValueError:
            raise ValueError(
                "Argument 'margin' must be a single non-negative integer (same margin for all four sides) or a 4-tuple of non-negative integers (specifying the top, right, bottom, and left margin).")

        # check padding
        try:
            (padding_vertical, padding_horizontal) = dito.utils.get_validated_tuple(x=padding, type_=int, count=2, min_value=0, max_value=None)
        except ValueError:
            raise ValueError("Argument 'padding' must be a single non-negative integer (same padding for both sides) or a 2-tuple of non-negative integers (specifying the vertical and horizontal padding).")

        # create foreground and background masks and images
        out_size = (
            (max_character_count * self.char_width) + (border_left + border_right) + (margin_left + margin_right) + max(0, max_character_count - 1) * padding_horizontal,
            (line_count * self.char_height) + (border_top + border_bottom) + (margin_top + margin_bottom) + max(0, line_count - 1) * padding_vertical,
        )
        foreground_mask = np.zeros(shape=out_size[::-1], dtype=np.uint8)
        foreground_image = dito.data.constant_image(size=out_size, color=foreground_color)
        if background_color is None:
            background_mask = np.zeros(shape=out_size[::-1], dtype=np.uint8)
            background_image = dito.data.constant_image(size=out_size, color=(0, 0, 0))
        else:
            background_mask = np.zeros(shape=out_size[::-1], dtype=np.uint8) + 255
            background_image = dito.data.constant_image(size=out_size, color=background_color)

        # fill mask, foregound, and background image
        for (n_row, line) in enumerate(lines):
            row_offset = n_row * self.char_height + border_top + margin_top + n_row * padding_vertical

            # determine column offset due to alignment
            if alignment == "left":
                alignment_col_offset = 0
            elif alignment == "center":
                alignment_col_offset = (max_character_count - character_counts[n_row]) // 2
            elif alignment == "right":
                alignment_col_offset = max_character_count - character_counts[n_row]
            else:
                raise ValueError("Invalid alignment '{}'".format(alignment))

            for (n_col, char) in enumerate(line):
                # determine mask indices for current character
                col_offset = (n_col + alignment_col_offset) * self.char_width + border_left + margin_left + n_col * padding_horizontal
                indices = (slice(row_offset, row_offset + self.char_height), slice(col_offset, col_offset + self.char_width))

                # get current character image
                char_image = self.get_char_image(char=char, style=styles[n_row][n_col])

                # update background mask and image
                current_background_color = background_colors[n_row][n_col]
                if current_background_color != background_color:
                    if current_background_color is None:
                        background_mask[indices] = 0
                    else:
                        background_mask[indices] = 255
                        background_image[indices] = dito.data.constant_image(size=dito.core.size(image=char_image), color=current_background_color)

                # update foreground mask
                foreground_mask[indices] = char_image

                # update foreground image (= foreground color)
                current_foreground_color = foreground_colors[n_row][n_col]
                if current_foreground_color != foreground_color:
                    if current_foreground_color is not None:
                        foreground_image[indices] = dito.data.constant_image(size=dito.core.size(image=char_image), color=current_foreground_color)
                    else:
                        background_mask[indices] = np.minimum(background_mask[indices], 255 - foreground_mask[indices])
                        foreground_mask[indices] = 0

        # if using outline background mode, dilate text mask to get background mask
        if background_as_outline:
            background_mask = np.minimum(background_mask, dito.processing.dilate(image=foreground_mask, shape=cv2.MORPH_ELLIPSE, size=max(3, char_image.shape[0] // 5)))

        # draw border
        foreground_mask[:border_top, :] = 255
        foreground_mask[(out_size[1] - border_bottom):, :] = 255
        foreground_mask[:, :border_left] = 255
        foreground_mask[:, (out_size[0] - border_right):] = 255
        for (n_channel, value) in enumerate(border_color):
            foreground_image[:border_top, :, n_channel] = value
            foreground_image[(out_size[1] - border_bottom):, :, n_channel] = value
            foreground_image[:, :border_left, n_channel] = value
            foreground_image[:, (out_size[0] - border_right):, n_channel] = value

        # rescale image if requested
        if scale is not None:
            foreground_mask = dito.core.resize(image=foreground_mask, scale_or_size=scale, interpolation_down=cv2.INTER_AREA, interpolation_up=cv2.INTER_AREA)
            foreground_image = dito.core.resize(image=foreground_image, scale_or_size=scale, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)
            background_mask = dito.core.resize(image=background_mask, scale_or_size=scale, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)
            background_image = dito.core.resize(image=background_image, scale_or_size=scale, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)

        # shrink to specified width if requested
        if (shrink_to_width is not None) and (out_size[0] > shrink_to_width):
            target_size = (shrink_to_width, out_size[1])
            foreground_mask = dito.core.resize(image=foreground_mask, scale_or_size=target_size, interpolation_down=cv2.INTER_AREA, interpolation_up=cv2.INTER_AREA)
            foreground_image = dito.core.resize(image=foreground_image, scale_or_size=target_size, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)
            background_mask = dito.core.resize(image=background_mask, scale_or_size=target_size, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)
            background_image = dito.core.resize(image=background_image, scale_or_size=target_size, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST)

        # convert uint8 masks to [0, 1]-float mask
        foreground_mask = dito.core.convert(image=foreground_mask, dtype=np.float32)
        background_mask = dito.core.convert(image=background_mask, dtype=np.float32)

        # if target image is grayscale, also convert fore- and background images
        if dito.core.is_gray(image=target_image):
            foreground_image = dito.core.as_gray(image=foreground_image)
            background_image = dito.core.as_gray(image=background_image)

        # rotate if requested
        if rotation is not None:
            if isinstance(rotation, int) and ((rotation % 90) == 0):
                angle_normed = rotation % 360
                if angle_normed == 0:
                    rotation_func = None
                elif angle_normed == 90:
                    rotation_func = dito.core.rotate_90
                elif angle_normed == 180:
                    rotation_func = dito.core.rotate_180
                elif angle_normed == 270:
                    rotation_func = dito.core.rotate_270
            else:
                rotation_func = lambda image: dito.core.rotate(image=image, angle_deg=rotation, padding_mode="tight")

            if rotation_func is not None:
                foreground_mask = rotation_func(image=foreground_mask)
                foreground_mask = dito.core.clip_01(image=foreground_mask)
                foreground_image = rotation_func(image=foreground_image)

                background_mask = rotation_func(image=background_mask)
                background_mask = dito.core.clip_01(image=background_mask)
                background_image = rotation_func(image=background_image)

        # insert text into target image
        text_image = insert(
            target_image=background_image,
            source_image=foreground_image,
            position=(0, 0),
            anchor="lt",
            source_mask=foreground_mask,
        )
        text_mask = np.maximum(foreground_mask, background_mask)
        result_image = insert(
            target_image=target_image,
            source_image=dito.core.convert(image=text_image, dtype=target_image.dtype),
            position=position,
            anchor=anchor,
            source_mask=text_mask * opacity if opacity is not None else text_mask,
        )

        return result_image


def text(image, message, position=(0.0, 0.0), anchor="lt", font="source-25", style="regular", color=(235, 235, 235), background_color=(45, 45, 45), background_as_outline=False, border_color=(255, 255, 255), border=(0, 0, 0, 0), margin=(0, 0, 0, 0), padding=(0, 0), opacity=1.0, alignment="left", scale=None, rotation=None, shrink_to_width=None):
    """
    Render a text `message` into `image`.

    This function is a wrapper for `MonospaceBitmapFont.render_into_image`.

    Parameters
    ----------
    image : numpy.ndarray
        The image into which the text message is to be rendered. The original `image` is not altered.
    message : str
        The text message to be rendered. Can contain ANSI escape codes to set text style and color.
    position : tuple of float or tuple of int, optional
        The position at which the text message is to be placed in the image, given as a 2D point coordinates (x, y).
        If the coordinates are floats, they are interpreted as fractions of the image size. The default is `(0.0, 0.0)`.
        See `insert` for more details.
    anchor : str, optional
        The anchor position of the text message within the image, given as a two-letter string following the pattern `[lcr][tcb]`.
        The default is `"lt"`. See `insert` for more details.
    font : MonospaceBitmapFont or str, optional
        The font to use for rendering the text message. This can be an instance of `MonospaceBitmapFont` or a string indicating the name of the font. The default is `"source-25"`.
    style : str, optional
        The style of the text message. The default is `"regular"`.
    color : tuple of int, optional
        The color of the text message in BGR format. The default is `(235, 235, 235)`.
    background_color : tuple of int or None, optional
        The background color of the text message in BGR format. If `None`, the background is transparent. The default is `(45, 45, 45)`.
    background_as_outline : bool, optional
        If `True`, the `background_color` will be used as an outline around the text message. The default is `False`.
    border_color : tuple of int, optional
        The color of the border around the text message in BGR format. The default is `(255, 255, 255)`.
    border : tuple of int, optional
        The width of the border (top, right, bottom, left) around the text message. The default is `(0, 0, 0, 0)`.
    margin : tuple of int, optional
        The margin (top, right, bottom, left) around the text message. The default is `(0, 0, 0, 0)`.
    padding : tuple of int, optional
        The padding (vertical, horizontal) for the text message. The default is `(0, 0)`.
    opacity : float or None, optional
        The opacity in the range [0.0, 1.0] of the text message. A value of `None` means full opacity (i.e., no transparency). The default is `1.0`.
    alignment : {"left", "center", "right"}, optional
        The text alignment of each line. The default is `"left"`.
    scale : float or tuple of int or None, optional
        The scaling factor or target size of the text. If `None`, apply no scaling. The default is `None`.
    rotation : int or float or None, optional
        The rotation angle (in degrees, counter-clockwise) of the text message. Default is `None`, meaning no rotation.
    shrink_to_width : int or None, optional
        If not `None`, the width of the text will be shrunk to fit the specified width. The default is `None`.

    Returns
    -------
    numpy.ndarray
        The resulting image with the rendered text message.
    """

    # get font
    if isinstance(font, str):
        # font is given as name -> resolve
        font = MonospaceBitmapFont.init_from_name(name=font)
    elif not isinstance(font, MonospaceBitmapFont):
        raise TypeError("Argument 'font' must be either an instance of 'MonospaceBitmapFont' or a string (the name of the font)")

    # render message into image
    return font.render_into_image(
        target_image=image,
        message=message,
        style=style,
        position=position,
        anchor=anchor,
        foreground_color=color,
        background_color=background_color,
        background_as_outline=background_as_outline,
        border_color=border_color,
        border=border,
        margin=margin,
        padding=padding,
        opacity=opacity,
        alignment=alignment,
        scale=scale,
        rotation=rotation,
        shrink_to_width=shrink_to_width,
    )


#
# image display
#


def get_screenres(fallback=(1920, 1080)):
    """
    Return the resolution (width, height) of the screen in pixels.

    See http://stackoverflow.com/a/3949983 for more info.
    If it can not be determined, assume 1920x1080.

    Parameters
    ----------
    fallback : tuple of int, optional
        A 2-tuple of integers representing the fallback resolution to use if the actual screen resolution cannot be
        determined. Default is `(1920, 1080)`.

    Returns
    -------
    tuple of int
        A 2-tuple of integers representing the width and height of the screen resolution in pixels.
    """

    try:
        import tkinter as tk
    except ImportError:
        return fallback

    try:
        root = tk.Tk()
    except tk.TclError:
        return fallback
    (width, height) = (root.winfo_screenwidth(), root.winfo_screenheight())
    root.destroy()
    return (width, height)


def qkeys():
    """
    Return a tuple of key codes corresponding to key presses indicating the desire to quit (`<ESC>`, `q`).

    The key codes are "unicode code points", as returned by the Python builtin `ord`.

    Returns
    -------
    tuple of int
        A tuple of two integers corresponding to the key codes of the
        keys that can be pressed to quit. The first integer corresponds
        to the ASCII code of the `<ESC>` key, and the second integer
        corresponds to the ASCII code of the `q` key.

    Examples
    --------
    >>> qkeys()
    (27, 113)
    """
    return (27, ord("q"))


def prepare_for_display(image, scale=None, normalize_mode=None, normalize_kwargs=dict(), colormap=None):
    """
    Prepare `image` (or a list or a list of lists of images) for being
    displayed on the screen (or similar purposes).

    This is an internal function used by `show` and `MultiShow`.

    Parameters
    ----------
    image : ndarray or tuple of ndarrays or tuple of tuples of ndarrays
        The image (or list of images or a list of lists of images) to be prepared. If multiple images are given, they are arranged into one image via `stack`.
    scale : float or tuple of int, optional
        The scaling factor or target size of the image, see `dito.core.resize`. If `None`, a scale factor is determined automatically.
    normalize_mode : str or None, optional
        The normalization mode to be used, see `dito.core.normalize`. If `None`, the image will not be normalized.
    normalize_kwargs : dict, optional
        Keyword arguments for the normalization function `dito.core.normalize`.
    colormap : str or None, optional
        The colormap to be applied to the image, see `colorize`. If `None`, no colormap will be applied.

    Returns
    -------
    ndarray
        The prepared image, ready to be displayed.
    """
    if isinstance(image, np.ndarray):
        # use image as is
        pass
    elif isinstance(image, (list, tuple)) and (len(image) > 0) and isinstance(image[0], np.ndarray):
        # list of images: stack them into one image
        image = stack(images=[image])
    elif isinstance(image, (list, tuple)) and (len(image) > 0) and isinstance(image[0], (list, tuple)) and (len(image[0]) > 0) and isinstance(image[0][0], np.ndarray):
        # list of lists of images: stack them into one image
        image = stack(images=image)
    else:
        raise ValueError("Invalid value for parameter `image` ({}) - it must either be (i) an image, (ii) a non-empty list of images or a non-empty list of non-empty lists of images".format(image))

    # OpenCV does not support the display of bool images - convert them to uint8
    if image.dtype == bool:
        image = dito.core.convert(image=image, dtype=np.uint8)

    # normalize intensity values
    if normalize_mode is not None:
        image = dito.core.normalize(image=image, mode=normalize_mode, **normalize_kwargs)

    # resize image
    if scale is None:
        # try to find a good scale factor automatically
        (width, height) = get_screenres()
        scale = 0.85 * min(height / image.shape[0], width / image.shape[1])
    image = dito.core.resize(image=image, scale_or_size=scale)

    # apply colormap
    if colormap is not None:
        image = colorize(image=image, colormap=colormap)

    return image


def showr(*args, **kwargs):
    return show(*args, raise_on_qkey=True, **kwargs)


def show(image, wait=0, scale=None, normalize_mode=None, normalize_kwargs=dict(), colormap=None, window_name=DEFAULT_WINDOW_NAME, close_window=False, engine=None, raise_on_qkey=False):
    """
    Display the image on the screen.

    Parameters
    ----------
    image : ndarray or tuple of ndarrays or tuple of tuples of ndarrays
        The image (or list of images or a list of lists of images) to be prepared. If multiple images are given, they are arranged into one image via `stack`.
    wait : int, optional
        The time in milliseconds to wait after showing the image. If `0`, wait indefinitely (until user key press). Default is `0`.
    scale : float or tuple of int, optional
        The scaling factor or target size of the image, see `dito.core.resize`. If `None`, a scale factor is determined automatically.
    normalize_mode : str or None, optional
        The normalization mode to be used, see `dito.core.normalize`. If `None`, the image will not be normalized.
    normalize_kwargs : dict, optional
        Keyword arguments for the normalization function `dito.core.normalize`.
    colormap : str or None, optional
        The colormap to be applied to the image, see `colorize`. If `None`, no colormap will be applied.
    window_name : str, optional
        The name of the window in which the image will be displayed. Default is `DEFAULT_WINDOW_NAME`.
    close_window : bool, optional
        If `True`, close the window after the image is displayed. Default is `False`.
    engine : str, optional
        The backend to use for displaying the image. Possible backends are
        - OpenCV (None, `"cv2"`),
        - Matplotlib (`"matplotlib"`, `"plt"`),
        - Jupyter (`"ipython"`, `"jupyter"`), and
        - PyGame (`"pygame"`).
        Default is `None`, which means OpenCV.
    raise_on_qkey : bool, optional
        If `True`, raise a `dito.exceptions.QkeyInterrupt` exception if the user presses a "quit" key (see `qkeys`)
        during the display. Default is `False`.

    Returns
    -------
    int
        The key code of the last key pressed during the display, or `-1` if no key was pressed.

    Raises
    ------
    RuntimeError
        If an unsupported `engine` is selected.
    dito.exceptions.QkeyInterrupt
        If `raise_on_qkey` is `True` and the user presses a "quit" key during the display.
    """

    image_show = prepare_for_display(image=image, scale=scale, normalize_mode=normalize_mode, normalize_kwargs=normalize_kwargs, colormap=colormap)

    # determine how to display the image
    if engine is None:
        # TODO: auto-detect if in notebook
        engine = "cv2"

    # show
    if engine in ("cv2",):
        try:
            cv2.imshow(window_name, image_show)
            key = cv2.waitKey(wait)
        finally:
            if close_window:
                cv2.destroyWindow(window_name)

    elif engine in ("matplotlib", "plt"):
        import matplotlib.pyplot as plt
        plt.imshow(X=dito.core.flip_channels(image=image_show))
        plt.tight_layout()
        plt.show()
        key = -1

    elif engine in ("ipython", "jupyter"):
        # source: https://gist.github.com/uduse/e3122b708a8871dfe9643908e6ef5c54
        import io
        import IPython.display

        image_show_encoded = dito.io.encode(image=image_show, extension="png")
        image_show_bytes = io.BytesIO()
        image_show_bytes.write(image_show_encoded)
        IPython.display.display(IPython.display.Image(data=image_show_bytes.getvalue()))
        key = -1

    elif engine in ("pygame",):
        import io
        import pygame

        # convert NumPy array of image to pygame surface
        image_show = dito.core.as_color(image=image_show)
        image_pygame = pygame.image.frombuffer(image_show.tobytes(), dito.core.size(image_show), "BGR")

        # set up pygame window
        pygame.display.set_caption(window_name)
        image_icon = pygame.image.frombuffer(dito.core.resize(image=image_show, scale_or_size=(32, 32), interpolation_down=cv2.INTER_NEAREST).tobytes(), (32, 32), "BGR")
        pygame.display.set_icon(image_icon)

        # draw image
        display_surface = pygame.display.set_mode(dito.core.size(image=image_show))
        display_surface.fill((0, 0, 0))
        display_surface.blit(image_pygame, (0, 0))
        pygame.display.flip()

        # emulate same behavior as OpenCV when keeping keys pressed
        pygame.key.set_repeat(500, 10)

        # wait for input
        while True:
            # wait after showing the image
            if wait > 0:
                pygame.time.wait(wait)
            else:
                pygame.time.wait(10)

            # return key code if key was pressed during the wait phase
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    return event.key

            # if no key was pressed and wait > 0, return -1 (this is equivalent to OpenCV's behavior)
            if wait > 0:
                return -1

    else:
        raise RuntimeError("Unsupported engine '{}'".format(engine))

    if raise_on_qkey and (key in qkeys()):
        raise dito.exceptions.QkeyInterrupt()

    return key


class MultiShow():
    """
    Extension of the functionality provided by the `dito.show` function.

    It keeps all images that have been shown and can re-show them interactively.
    """

    def __init__(self, window_name="dito.MultiShow", close_window=False, engine="cv2", save_dir=None):
        """
        Initializes a new MultiShow object.

        Parameters
        ----------
        window_name : str, optional
            Name of the window used to display the images. The default value is `"dito.MultiShow"`.
        close_window : bool, optional
            Whether the window should be closed after the last image has been displayed. The default value is `False`.
        engine : str, optional
            Name of the image display engine to use, see `show`. The default value is `"cv2"`.
        save_dir : str or None, optional
            Directory where images should be saved. If `None` (default), a temporary directory will be created when the user requests to save the images.

        Returns
        -------
        MultiShow
            A new MultiShow object.
        """
        self.window_name = window_name
        self.close_window = close_window
        self.engine = engine
        self.save_dir = save_dir
        self.images = []

    def save(self, n_image, verbose=True):
        """
        Save the `n_image`-th image to a file.

        Parameters
        ----------
        n_image : int
            Index of the image to save.
        verbose : bool, optional
            Whether to print information about the saved file. The default value is `True`.

        Returns
        -------
        None
        """
        if self.save_dir is None:
            self.save_dir = dito.utils.get_temp_dir(prefix="dito.MultiShow.{}.".format(dito.utils.now_str())).name
        filename = os.path.join(self.save_dir, "{:>08d}.png".format(n_image + 1))
        dito.io.save(filename=filename, image=self.images[n_image])
        if verbose:
            print("Saved image {}/{} to file '{}'".format(n_image + 1, len(self.images), filename))

    def save_all(self, **kwargs):
        """
        Save all images to files.

        Parameters
        ----------
        **kwargs : dict, optional
            Additional keyword arguments to pass to the `MultiShow.save` method.

        Returns
        -------
        None
        """
        for n_image in range(len(self.images)):
            self.save(n_image=n_image, **kwargs)

    def _show(self, image, wait, engine):
        """
        Internal method used to actually show an image on the screen.

        Parameters
        ----------
        image : numpy.ndarray
            Image to show.
        wait : int
            Time to wait after showing the image (in milliseconds), see `show`.
        engine : str
            Name of the image display engine to use, see `show`.

        Returns
        -------
        int
            Key code of the last key pressed, or -1 if no key was pressed.

        See Also
        --------
        `show` : Function used to display the image.
        """
        return show(image=image, wait=wait, scale=1.0, normalize_mode=None, normalize_kwargs=dict(), colormap=None, window_name=self.window_name, close_window=self.close_window, engine=engine)

    def show(self, image, wait=0, scale=None, normalize_mode=None, normalize_kwargs=dict(), colormap=None, keep=True, hide=False):
        """
        Show `image` on the screen, just as `dito.visual.show` would.

        In addition, the image is also stored internally, and can be re-shown anytime.

        Parameters
        ----------
        keep : bool, optional
            If `True` (the default), store the image internally so that it can be re-shown later.
        hide : bool, optional
            If `True`, do not show the image, but store it anyway (if `keep=True`). Defaults to `False`.

        Returns
        -------
        int
            Key code of the last key pressed, or -1 if no key was pressed. See `MultiShow._show`.

        See Also
        --------
        `dito.visual.show` : For a description of all other parameters.
        """
        image_show = prepare_for_display(image=image, scale=scale, normalize_mode=normalize_mode, normalize_kwargs=normalize_kwargs, colormap=colormap)
        if keep:
            self.images.append(image_show)
        if not hide:
            return self._show(image=image_show, wait=wait, engine=self.engine)
        else:
            return -1

    def reshow(self, n_image, wait=0):
        """
        Re-show a specific image from the stored images.

        Parameters
        ----------
        n_image : int
            Index of the image to be re-shown.
        wait : int, optional
            Delay in milliseconds after showing the image (default is `0`, meaning to wait until keypress, see `dito.visual.show`).

        Returns
        -------
        int
            Key code of the last key pressed, or -1 if no key was pressed. See `MultiShow._show`.
        """
        return self._show(image=self.images[n_image], wait=wait, engine=self.engine)

    def reshow_interactive(self):
        """
        Re-show all stored images of this `MultiShow` instance interactively.

        Displays all images one by one, allowing the user to interactively
        navigate between the images using the following keys:
        - `+`: show the next image
        - `-`: show the previous image
        - ` ` (space): toggle overlay displaying the image index
        - `s`: save the current image to a file
        - `a`: save all images to files
        - `q` or `ESC`: quit the interactive mode
        """
        image_count = len(self.images)
        if image_count == 0:
            raise RuntimeError("No images available")

        # initial settings
        n_image = image_count - 1
        show_overlay = True

        # start loop
        while True:
            # get image to show
            image = self.images[n_image]
            if show_overlay:
                image = text(image=image, message="{}/{}".format(n_image + 1, image_count), scale=0.5)

            # show image (we need "cv2" as engine, to capture the keyboard inputs)
            key = self._show(image=image, wait=0, engine="cv2")

            # handle keys
            if key in (ord("+"),):
                # show next image
                n_image = (n_image + 1) % image_count
            elif key in (ord("-"),):
                # show previous image
                n_image = (n_image - 1) % image_count
            elif key in (ord(" "),):
                # toggle overlay
                show_overlay = not show_overlay
            elif key in (ord("s"),):
                # save current image
                self.save(n_image=n_image)
            elif key in (ord("a"),):
                # save all images
                self.save_all()
            elif key in qkeys():
                # quit
                break

            if self.close_window:
                cv2.destroyWindow(winname=self.window_name)
