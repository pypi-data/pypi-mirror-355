"""
This submodule provides essential tools and helpers for OpenCV images represented as NumPy arrays.
"""
import re

import cv2
import numpy as np

import dito.exceptions
import dito.utils


#
# general
#


def is_image(image):
    """
    Determine if given image is a valid grayscale or color image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.

    Returns
    -------
    bool
        Returns `True` if input image is valid grayscale or color image.
    """
    
    return is_gray(image=image) or is_color(image=image)


#
# type-related
#


def is_integer_dtype(dtype):
    """
    Check if the input data type is an integer type.

    Parameters
    ----------
    dtype : numpy.dtype
        Input data type.

    Returns
    -------
    bool
        Returns `True` if input data type is an integer type.

    Examples
    --------
    >>> is_integer_dtype(np.uint8)
    True

    >>> is_integer_dtype(np.int16)
    True

    >>> is_integer_dtype(np.float32)
    False

    >>> is_integer_dtype(bool)
    False
    """
    return np.issubdtype(dtype, np.integer)


def is_integer_image(image):
    """
    Check if the data type of the input image is an integer type.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.

    Returns
    -------
    bool
        Returns `True` if input image data type is an integer type.
    """
    return is_integer_dtype(dtype=image.dtype)


def is_float_dtype(dtype):
    """
    Check if the input data type is a floating-point type.

    Parameters
    ----------
    dtype : numpy.dtype
        Input data type.

    Returns
    -------
    bool
        Returns `True` if input data type is a floating-point type.
    """
    return np.issubdtype(dtype, np.floating)


def is_float_image(image):
    """
    Check if the data type of the input image is a floating-point type.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.

    Returns
    -------
    bool
        Returns `True` if input image data type is a floating-point type.
    """
    return is_float_dtype(dtype=image.dtype)


def is_bool_dtype(dtype):
    """
    Check if the input data type is a boolean type.

    Parameters
    ----------
    dtype : numpy.dtype
        Input data type.

    Returns
    -------
    bool
        Returns `True` if input data type is a boolean type.
    """
    return np.issubdtype(dtype, np.bool_)


def is_bool_image(image):
    """
    Check if the data type of the input image is a boolean type.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.

    Returns
    -------
    bool
        Returns `True` if input image data type is a boolean type.
    """
    return is_bool_dtype(dtype=image.dtype)


def dtype_range(dtype):
    """
    Returns the minimum and maximum intensity values of images for a given NumPy dtype.

    Parameters
    ----------
    dtype : numpy.dtype
        NumPy data type of input image.

    Returns
    -------
    tuple
        A tuple containing the minimum and maximum intensity values of the input dtype.
        For integer dtypes, this corresponds to their full range (`(0, 255)` for `numpy.uint8` or `(-128, 127)` for `numpy.int8`, etc.).
        For floating dtypes, this corresponds to the range `(0.0, 1.0)`.
        For boolean dtypes, this corresponds to the range `(False, True)`.

    Raises
    ------
    TypeError
        If the input dtype is not supported.

    Notes
    -----
    The returned values are inclusive.

    Examples
    --------
    >>> dtype_range(np.uint8)
    (0, 255)

    >>> dtype_range(np.int16)
    (-32768, 32767)

    >>> dtype_range(np.float32) == dtype_range(np.float64)
    True

    >>> dtype_range(bool)
    (False, True)
    """
    if is_integer_dtype(dtype=dtype):
        info = np.iinfo(dtype)
        return (info.min, info.max)
    elif is_float_dtype(dtype=dtype):
        return (0.0, 1.0)
    elif is_bool_dtype(dtype=dtype):
        return (False, True)
    else:
        raise TypeError("Unsupported dtype '{}'".format(dtype))


def dtype_common(dtypes):
    """
    Find the common data type that can represent all the given NumPy dtypes.

    Parameters
    ----------
    dtypes : list or tuple
        List of NumPy data types to be considered.

    Returns
    -------
    numpy.dtype
        The highest data type in the NumPy hierarchy that supports all the ranges
        of the input dtypes.

    Raises
    ------
    ValueError
        If an invalid dtype is encountered.

    Notes
    -----
    The hierarchy of supported NumPy data types, from lowest to highest, is:
    bool, uint8, uint16, float32, float64.

    Examples
    --------
    >>> dtype_common([np.uint8, np.uint8])
    <class 'numpy.uint8'>

    >>> dtype_common([np.uint8, np.uint16])
    <class 'numpy.uint16'>

    >>> dtype_common([np.uint8, np.float32])
    <class 'numpy.float32'>
    """

    hierarchy = (np.bool_, np.uint8, np.uint16, np.float32, np.float64)
    max_index = 0
    for dtype in dtypes:
        # check if `dtype` is a valid NumPy dtype
        try:
            np.dtype(dtype)
        except TypeError:
            raise ValueError("Invalid image type '{}'".format(dtype))

        # search for `dtype` in the hierarchy and update the max index if found
        for (index, value) in enumerate(hierarchy):
            if value == np.dtype(dtype):
                max_index = max(max_index, index)
                break
        else:
            raise ValueError("Invalid image type '{}'".format(dtype))
    return hierarchy[max_index]


def convert(image, dtype):
    """
    Convert input `image` to the NumPy `dtype` and scale the intensity values accordingly.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be converted.
    dtype : numpy.dtype
        Desired output data type of the image.

    Returns
    -------
    numpy.ndarray
        A copy of the input image with converted data type and scaled intensity values.

    Notes
    -----
    Intensity values are always clipped to the allowed range (even for identical source and target types).
    The returned image is always a copy of the data, even for equal source and target types.

    Example
    -------
    >>> image = np.array([[0.0, 1.0]], dtype=np.float32)
    >>> convert(image, np.uint8)
    array([[  0, 255]], dtype=uint8)
    """

    # clip image against its source dtype (important for floats)
    # clip also guarantees that the original image will remain unchanged
    (lower, upper) = dtype_range(dtype=image.dtype)
    image_clipped = clip(image=image, lower=lower, upper=upper)

    if image.dtype == dtype:
        return image_clipped
    else:
        # only a scale factor is needed, since all dtypes share a common "zero"
        scale = dtype_range(dtype=dtype)[1] / dtype_range(dtype=image.dtype)[1]

        # use at least the 'float32' dtype for the intermediate image (but if the image is 'float64', use that)
        intermediate_dtype = dtype_common(dtypes=[image.dtype, np.float32])

        return (image_clipped.astype(dtype=intermediate_dtype) * scale).astype(dtype)


#
# array access
#


def tir(*args):
    """
    Round the input arguments to the nearest integer, and combine them into a tuple.

    This function is primarily used to pass point coordinates to certain OpenCV functions.

    Parameters
    ----------
    *args : float or tuple
        Input arguments that will be rounded and combined into a tuple.
        If a single tuple of length 2 is provided, its elements will be used.
        If two separate arguments are provided, they will be used.

    Returns
    -------
    tuple
        A tuple containing the rounded integers of the input arguments.

    Raises
    ------
    ValueError
        If the input arguments are not valid.

    Examples
    --------
    >>> tir(1.24, -1.87)
    (1, -2)

    >>> tir([5.3, -9.9])
    (5, -10)
    """

    if (len(args) == 1) and (len(args[0]) == 2):
        items = args[0]
    elif len(args) == 2:
        items = args
    else:
        raise ValueError("The two required arguments must either be (i) given separately or (ii) via a sequence of length two, but got neither")
    return tuple(int(round(item)) for item in items)


#
# geometry related
#


def check_shape(image_or_shape, shape_def):
    """
    Validate that a given shape matches the specified shape definition.

    Parameters
    ----------
    image_or_shape : numpy.ndarray or tuple
        The input image or shape tuple to validate.
    shape_def : str
        The shape definition string, describing expected dimensions, names, and/or values. See `parse_shape()` for
        details.

    Returns
    -------
    None
        Returns nothing if the shape is valid. Raises an error if the shape does not match the definition.

    Raises
    ------
    TypeError
        If the inputs are not of expected types.
    dito.exceptions.ParseShapeDefinitionError
        If the shape definition string is malformed.
    dito.exceptions.ParseShapeMismatchError
        If the actual shape does not match the definition.
    """
    parse_shape(image_or_shape=image_or_shape, shape_def=shape_def)


def parse_shape(image_or_shape, shape_def):
    """
    Parse and validate a shape against a textual shape definition, and collect axis sizes into a dictionary using the
    axis names of the shape definition as keys.

    Parameters
    ----------
    image_or_shape : numpy.ndarray or tuple
        The shape to validate. Can be a NumPy image (uses `.shape`) or a shape tuple.
    shape_def : str
        A space-separated shape definition string. Each part describes one axis, and may be:
        - An axis name without value constraint (e.g., `h` or `height`): accepts any value and is collected into the result.
        - An unnamed value constraint (e.g., `3` or `1|3|5`): requires the axis to match one of the given sizes.
        - An axis name with value constraint (e.g., `c=1|3` or `d=256`): must match one of the values and is collected.

        Special symbols and rules:
        - `...` (ellipsis) may appear once to absorb zero or more axes; these are neither validated nor collected.
        - `_` is a special named placeholder axis. It may be used multiple times, and is not collected into the output dict.
        - Axis names must match `[a-zA-Z_]+` and be unique except `_`, which can repeat.

    Returns
    -------
    dict
        A dictionary mapping axis names (excluding `_` and ellipsis-absorbed axes) to their sizes.

    Raises
    ------
    TypeError
        If input types are invalid.
    dito.exceptions.ParseShapeDefinitionError
        If the shape definition is malformed (e.g., invalid syntax, duplicate names).
    dito.exceptions.ParseShapeMismatchError
        If the shape does not match the constraints in the definition.

    Examples
    --------
    >>> parse_shape((224, 224, 3), "h w 3")
    {'h': 224, 'w': 224}

    >>> parse_shape((224, 224, 3), "h w c=3")
    {'h': 224, 'w': 224, 'c': 3}

    >>> parse_shape((224, 224, 1), "h w c=1|3")
    {'h': 224, 'w': 224, 'c': 1}

    >>> parse_shape((224, 224, 3), "h w ...")
    {'h': 224, 'w': 224}

    >>> parse_shape((224, 224, 3), "h w c ...")
    {'h': 224, 'w': 224, 'c': 3}

    >>> parse_shape((8, 224, 224, 3), "batch=8 ... channel=3")
    {'batch': 8, 'channel': 3}

    >>> parse_shape((1, 14, 28), "1 _ 28")
    {}

    >>> parse_shape((224, 224, 3), "... c")
    {'c': 3}
    """

    # check types
    if isinstance(image_or_shape, np.ndarray):
        image_shape = image_or_shape.shape
    elif isinstance(image_or_shape, tuple):
        image_shape = image_or_shape
    else:
        raise TypeError("Argument 'image_or_shape' must be an image or a tuple, but is of type '{}'".format(type(image_or_shape)))

    if not isinstance(shape_def, str):
        raise TypeError("Argument 'shape_def' must be a string")

    shape_def_parts = shape_def.strip().split()

    # check if shape definition contains an ellipsis
    ellipsis_index = None
    for (n_part, shape_def_part) in enumerate(shape_def_parts):
        if shape_def_part == "...":
            if ellipsis_index is None:
                ellipsis_index = n_part
            else:
                raise dito.exceptions.ParseShapeDefinitionError(f"Shape definition must not contain more than one ellipsis ('...'), but is: '{shape_def}'")

    # check if the lengths of the shape and the shape definition are compatible
    if (
        (ellipsis_index is None) and (len(image_shape) != len(shape_def_parts))
    ) or (
        (ellipsis_index is not None) and ((len(shape_def_parts) - 1) > len(image_shape))
    ):
        raise dito.exceptions.ParseShapeMismatchError(f"Shape definition '{shape_def}' and shape '{image_shape}' have conflicting lengths")

    # if there is an ellipsis in the shape definition, fill in the missing parts
    if ellipsis_index is not None:
        missing_part_count = len(image_shape) - (len(shape_def_parts) - 1)
        shape_def_parts = shape_def_parts[:ellipsis_index] + (["_"] * missing_part_count) + shape_def_parts[(ellipsis_index + 1):]

    # this should not happen, but let's better check it
    if len(shape_def_parts) != len(image_shape):
        raise RuntimeError("Internal error: shape definition length and image shape length differ after ellipsis expansion")

    # parse every part of the shape definition
    shape_def_paramss = []
    for shape_def_part in shape_def_parts:
        # a shape_def part can contain:
        # - just a name (e.g., "c"), or
        # - just a value definition (e.g., "1|3"), or
        # - both a name and a value definition (e.g., "c=1|3"),
        # and the value definition must be:
        # - a non-negative int, or
        # - non-negative ints, separated by "|"

        # for the current shape definition part, get the name (if specified) and/or the value string (if specified)
        # it is possible that both are specified (e.g., "c=1|3") or that only one of them is specified ("c" or "1|3")
        name_pattern = r"[a-zA-Z_]+"
        if "=" in shape_def_part:
            # the shape definition part contains both a name and a value specification
            (part_name, part_value_str) = shape_def_part.split("=", 1)
        else:
            # the shape definition part contains either a name or a value specification, and we need to find out which
            name_match = re.fullmatch(name_pattern, shape_def_part)
            if name_match is not None:
                # it is just the name
                (part_name, part_value_str) = (shape_def_part, None)
            else:
                # otherwise, it must be a value string
                (part_name, part_value_str) = (None, shape_def_part)

        # verify the name (if it is specified)
        if part_name is not None:
            name_match = re.fullmatch(name_pattern, part_name)
            if name_match is None:
                raise dito.exceptions.ParseShapeDefinitionError(f"Invalid axis name '{part_name}' in part '{shape_def_part}' of shape definition '{shape_def}'")

        # special case: part name "_" is treated as no name (-> placeholder)
        if (part_name is not None) and (part_name == "_"):
            part_name = None

        # verify the number part (if it is specified)
        if part_value_str is None:
            part_values = None
        else:
            # try to parse one or multiple numbers separated by "|"
            pipe_parts = part_value_str.split("|")

            # check for empty parts after pipe splitting (e.g., caused by "3|" or "3||4")
            if any(pipe_part == "" for pipe_part in pipe_parts):
                raise dito.exceptions.ParseShapeDefinitionError(f"Missing numeric value in part '{shape_def_part}' of shape definition '{shape_def}' (possibly caused by '|' not being surrounded by a number on each side)")

            # parse integers
            try:
                part_values = [int(pipe_part) for pipe_part in pipe_parts]
            except ValueError:
                raise dito.exceptions.ParseShapeDefinitionError(f"Invalid numeric value in part '{shape_def_part}' of shape definition '{shape_def}'")

            # make sure that the integers are non-negative
            for value in part_values:
                if value < 0:
                    raise dito.exceptions.ParseShapeDefinitionError(f"Negative numeric value in part '{shape_def_part}' of shape definition '{shape_def}'")

        # save name (possibly None) and list of allowed values (possibly None, meaning "any")
        # for the current shape definition part
        shape_def_paramss.append({
            "name": part_name,
            "part_values": part_values,
        })

    # check each entry of the shape and fill collect values for named shape definition parts
    axis_names_to_sizes = {}
    for (n_axis, (axis_size, shape_def_params)) in enumerate(zip(image_shape, shape_def_paramss)):
        axis_name = shape_def_params["name"]
        axis_size_constraints = shape_def_params["part_values"]

        # if name for the current axis is given in the shape definition, collect the actual axis size
        if axis_name is not None:
            if axis_name in axis_names_to_sizes.keys():
                raise dito.exceptions.ParseShapeDefinitionError(f"Duplicate axis name '{axis_name}' in shape definition '{shape_def}")
            axis_names_to_sizes[axis_name] = axis_size

        # if there are no value constraints for the current axis, proceed without error
        if axis_size_constraints is None:
            continue

        # if there are value constraints for the current axis, raise an error of they are violated
        if axis_size not in axis_size_constraints:
            raise dito.exceptions.ParseShapeMismatchError(f"Shape mismatch ({axis_size} vs. {'|'.join(str(constraint) for constraint in axis_size_constraints)}) for axis index {n_axis} {'(' + axis_name + ') ' if axis_name is not None else ''}between image shape '{image_shape}' and shape definition '{shape_def}'")

    return axis_names_to_sizes


def size(image):
    """
    Return the size (width x height) of the input image as a tuple.

    Parameters
    ----------
    image : numpy.ndarray
        The input image.

    Returns
    -------
    tuple
        A tuple containing the size `(width, height)` of the input image.

    Examples
    --------
    >>> image = np.zeros((480, 640), dtype=np.uint8)
    >>> size(image)
    (640, 480)

    >>> image = np.zeros((720, 1280, 3), dtype=np.float32)
    >>> size(image)
    (1280, 720)
    """
    return (image.shape[1], image.shape[0])


def resize(image, scale_or_size, interpolation_down=cv2.INTER_CUBIC, interpolation_up=cv2.INTER_NEAREST):
    """
    Resize the input image to a new size or by a scaling factor.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be resized.
    scale_or_size : float or tuple
        If `scale_or_size` is a float, it represents the scaling factor by which to resize the image.
        If `scale_or_size` is a tuple, it represents the target size `(width, height)` of the output image.
    interpolation_down : int, optional
        Interpolation method used when scaling the image down. Default is `cv2.INTER_CUBIC`.
    interpolation_up : int, optional
        Interpolation method used when scaling the image up. Default is `cv2.INTER_NEAREST`.

    Returns
    -------
    numpy.ndarray
        The resized image.

    Raises
    ------
    ValueError
        If the input arguments are not valid.

    Examples
    --------
    >>> image = np.zeros((480, 640), dtype=np.uint8)
    >>> resized_image = resize(image, 0.5)
    >>> size(resized_image)
    (320, 240)

    >>> image = np.zeros((480, 640), dtype=np.float32)
    >>> resized_image = resize(image, (800, 600))
    >>> size(resized_image)
    (800, 600)
    """

    # OpenCV does not support resizing of bool images - this is a workaround
    if image.dtype == bool:
        image_uint8 = image.astype(np.uint8)
        image_uint8 = resize(image=image_uint8, scale_or_size=scale_or_size, interpolation_down=interpolation_down, interpolation_up=interpolation_up)
        return image_uint8 > 0

    # resize by scale factor
    if isinstance(scale_or_size, float):
        scale = scale_or_size
        return cv2.resize(src=image, dsize=None, dst=None, fx=scale, fy=scale, interpolation=interpolation_up if scale > 1.0 else interpolation_down)

    # resize to target size
    elif isinstance(scale_or_size, tuple) and (len(scale_or_size) == 2):
        target_size = scale_or_size
        current_size = size(image)
        return cv2.resize(src=image, dsize=target_size, dst=None, fx=0.0, fy=0.0, interpolation=interpolation_up if all(target_size[n_dim] > current_size[n_dim] for n_dim in range(2)) else interpolation_down)
    
    else:
        raise ValueError("Expected a float (= scale factor) or a 2-tuple (= target size) for argument 'scale_or_size', but got type '{}'".format(type(scale_or_size)))


class PaddedImageIndexer():
    """
    Wrapper for an `np.ndarray` which allows indexing out-of-bounds and returns
    a padded image.
    """

    def __init__(self, image, pad_kwargs=None):
        """
        Parameters
        ----------
        image : numpy.ndarray
            Input image to be indexed and padded.
        pad_kwargs : dict, optional
            Additional keyword arguments to pass to `np.pad()` function. Default is `None`.

        Raises
        ------
        AssertionError
            If the input `image` is not a valid NumPy array.
        """
        self.image = image
        self.pad_kwargs = pad_kwargs
        if self.pad_kwargs is None:
            self.pad_kwargs = {}

        assert isinstance(self.image, np.ndarray)

    def __getitem__(self, item):
        """
        Return a cropped and padded version of the input image according to the given indices.

        Parameters
        ----------
        item : tuple of slices (with one ellipsis allowed) or slice or ellipsis
            Index tuple to extract the subregion from the image.

        Returns
        -------
        numpy.ndarray
            A cropped and padded version of the image.

        Raises
        ------
        IndexError
            If more than one ellipsis is used.
        ValueError
            If the indices are invalid.
        TypeError
            If any of the indices are not slices.
        """
        if isinstance(item, tuple):
            indices = item
        elif isinstance(item, slice):
            indices = (item,)
        elif item is Ellipsis:
            indices = tuple()
        else:
            raise ValueError("Index must be either a (i) tuple of slices (with optional ellipsis), (ii) a slice, or (iii) an ellipsis, but is of type '{}'".format(type(item)))

        axis_count = len(self.image.shape)

        # find and replace Ellipsis
        ellipsis_positions = []
        for (n_axis, index) in enumerate(indices):
            if isinstance(index, type(Ellipsis)):
                ellipsis_positions.append(n_axis)
        if len(ellipsis_positions) == 1:
            ellipsis_position = ellipsis_positions[0]
            ellipsis_axis_span = axis_count - len(indices)
            indices = tuple(indices[:ellipsis_position]) + tuple([slice(None, None, None)] * ellipsis_axis_span) + tuple(indices[(ellipsis_position + 1):])
        elif len(ellipsis_positions) > 1:
            raise IndexError("An index can only have a single ellipsis ('...')")

        # add slices (::) for missing axes
        if len(indices) < axis_count:
            indices = list(indices)
            while len(indices) < axis_count:
                indices.append(slice(None, None, None))
            indices = tuple(indices)
        elif len(indices) > axis_count:
            raise ValueError("The axis count ({}) is larger than the axis count of the image ({})".format(len(indices), axis_count))

        # for each axis collect the in-bound cropping indices and the pad widths
        pad_widths = []
        indices_after_padding = []
        for (n_axis, index) in enumerate(indices):
            if not isinstance(index, slice):
                raise TypeError("All indices must be slices, but index #{} is of type '{}'".format(n_axis, type(index).__name__))
            if (index.step is not None) and (index.step < 0):
                raise ValueError("Negative step sizes are currently not supported, but index #{} has step size {}".format(n_axis, index.step))

            axis_size = self.image.shape[n_axis]

            # replace None entries of the slice with numbers
            start = index.start if (index.start is not None) else 0
            stop = index.stop if (index.stop is not None) else axis_size
            step = index.step if (index.step is not None) else 1

            if start > stop:
                raise ValueError("Slice start ({}) is larger than slice stop ({})".format(start, stop))

            # store pad widths and crop indices
            pad_before = max(0, -start)
            pad_after = max(0, stop - axis_size)
            pad_widths.append((pad_before, pad_after))
            indices_after_padding.append(slice(start + pad_before, stop + pad_before, step))

        # apply padding where necessary
        image_padded = np.pad(array=self.image, pad_width=pad_widths, **self.pad_kwargs)

        # perform a valid crop within the padded image
        image_cropped = image_padded[tuple(indices_after_padding)]

        return image_cropped


def pad(image, count=None, count_top=None, count_right=None, count_bottom=None, count_left=None, mode=cv2.BORDER_CONSTANT, constant_value=0):
    """
    Pads an image with a border.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be padded.
    count : int, optional
        Number of pixels to add to all sides of the image. Cannot be set at the same time as `count_top`, `count_right`, `count_bottom` or `count_left`.
    count_top : int, optional
        Number of pixels to add to the top of the image.
    count_right : int, optional
        Number of pixels to add to the right of the image.
    count_bottom : int, optional
        Number of pixels to add to the bottom of the image.
    count_left : int, optional
        Number of pixels to add to the left of the image.
    mode : str or int, optional
        Border mode to use for padding. Can be either a string containing the mode name, or one of the constants defined in `cv2.BORDER_*`. Default is `cv2.BORDER_CONSTANT`.
        Example border modes:
            - 'constant': Pad with a constant value (specified by the `constant_value` argument).
            - 'replicate': Replicate the edge pixels.
            - 'reflect': Reflect the image, so that the border pixels are the mirror images of the interior pixels.
            - 'reflect_101': Same as 'reflect', but with the edge pixels not being replicated.
            - 'wrap': Wrap the image around itself.
    constant_value : scalar or sequence, optional
        Border color for the border mode `cv2.BORDER_CONSTANT`. Default is 0.

    Returns
    -------
    numpy.ndarray
        The padded image.

    Raises
    ------
    ValueError
        If the `count` argument is set along with `count_top`, `count_right`, `count_bottom` or `count_left`.
        If the `mode` argument is invalid.

    Examples
    --------
    >>> my_image = np.zeros((10, 10, 3), dtype=np.uint8)
    >>> padded_image = pad(image=my_image, count=1)
    >>> size(padded_image)
    (12, 12)

    >>> padded_image = pad(image=my_image, count_top=1, count_right=2, count_bottom=3, count_left=4, mode='reflect101')
    >>> size(padded_image)
    (16, 14)

    >>> padded_image = pad(image=my_image, count=2, constant_value=(255, 0, 0))
    >>> padded_image[0, 0, :]
    array([255,   0,   0], dtype=uint8)
    """

    if isinstance(mode, int):
        # assume mode to be one of cv2.BORDER_*
        pass
    elif isinstance(mode, str):
        attr_name = "BORDER_{}".format(mode.upper())
        mode = getattr(cv2, attr_name)
    else:
        raise ValueError("Invalid border mode '{}'".format(mode))

    trbl_all_none = (count_top is None) and (count_right is None) and (count_bottom is None) and (count_left is None)

    if (count is not None) and trbl_all_none:
        # padding counts are given by argument 'count'
        (count_top, count_right, count_bottom, count_left) = dito.utils.get_validated_tuple(x=count, type_=int, count=4, min_value=0, max_value=None)
    elif (count is None) and (not trbl_all_none):
        # padding counts are given by argument 'count_*'
        count_top = 0 if (count_top is None) else count_top
        count_right = 0 if (count_right is None) else count_right
        count_bottom = 0 if (count_bottom is None) else count_bottom
        count_left = 0 if (count_left is None) else count_left
    else:
        raise ValueError("If argument 'count' is set, arguments 'top', 'right', 'bottom', 'left' must be unset (None) and vice versa")

    return cv2.copyMakeBorder(src=image, top=count_top, bottom=count_bottom, left=count_left, right=count_right, borderType=mode, value=constant_value)


def center_pad_to(image, target_size, **kwargs):
    """
    Pad `image` to the `target_size` by adding borders on all sides such that the image is centered.

    If the `image` is larger than the `target_size` in any dimension, it will remain unmodified in that dimension.
    The padding parameters which are passed to `pad` can be given via `**kwargs`.

    Parameters
    ----------
    image : np.ndarray
        Input image to be padded.
    target_size : tuple of int
        The size that the output image should have.
    **kwargs
        Additional keyword arguments to be passed to the `pad` function.

    Returns
    -------
    np.ndarray
        Padded image with the specified size.

    See Also
    --------
    pad : Function that performs the padding operation.
    """

    missing_width = max(0, target_size[0] - image.shape[1])
    missing_height = max(0, target_size[1] - image.shape[0])

    count_top = missing_height // 2
    count_bottom = missing_height - count_top
    count_left = missing_width // 2
    count_right = missing_width - count_left

    return pad(image=image, count=None, count_top=count_top, count_right=count_right, count_bottom=count_bottom, count_left=count_left, **kwargs)


def center_crop_to(image, target_size):
    """
    Extract a center crop from the input `image`.

    If the `image` is smaller than the `target_size` in any dimension, the returned
    image will be cropped to the size of the `image` in that dimension.

    Parameters
    ----------
    image : np.ndarray
        Input image to be cropped.
    target_size : tuple of int
        The size of the output crop.

    Returns
    -------
    np.ndarray
        Center crop of the specified size.

    """

    image_size = size(image=image)
    indices = [None, None, Ellipsis]
    for n_dim in range(2):
        offset = max(0, image_size[n_dim] - target_size[n_dim]) // 2
        indices[1 - n_dim] = slice(offset, min(image_size[n_dim], offset + target_size[n_dim]))
    return image[tuple(indices)]


def center_pad_crop_to(image, target_size, **kwargs):
    """
    Center pad and crop the `image` so that the result is exactly of size `target_size`.

    Parameters
    ----------
    image : np.ndarray
        Input image to be padded and cropped.
    target_size : tuple of int
        The size of the output image.
    **kwargs
        Additional keyword arguments to be passed to the `center_pad_to` function.

    Returns
    -------
    np.ndarray
        Center crop of the specified size from the padded image.

    See Also
    --------
    center_pad_to : Function that performs the padding operation.
    center_crop_to : Function that performs the cropping operation.
    """

    image_padded = center_pad_to(image=image, target_size=target_size, **kwargs)
    image_cropped = center_crop_to(image=image_padded, target_size=target_size)
    return image_cropped


def rotate(image, angle_deg, padding_mode=None, interpolation=cv2.INTER_CUBIC):
    """
    Rotate the given `image` by an arbitrary angle given in degrees.

    Parameters
    ----------
    image : np.ndarray
        Input image to be rotated.
    angle_deg : float
        Rotation angle in degrees.
    padding_mode : {'tight', 'full', None}, optional
        The padding mode to use when rotating the image. If 'tight', the image is padded to exactly fit the rotated image.
        If 'full', the image is padded such that any rotation would fit. If None, no padding is performed. Default is None.
    interpolation : int, optional
        Interpolation method to use. See `cv2.warpAffine()` for valid options.
        Defaults to `cv2.INTER_CUBIC`.

    Returns
    -------
    np.ndarray
        Rotated image.

    Raises
    ------
    ValueError
        If `padding_mode` is not one of None, 'tight', or 'full'.

    See Also
    --------
    cv2.getRotationMatrix2D : Function to get the 2D rotation matrix.
    cv2.warpAffine : Function that performs the image rotation.
    """

    image_size = size(image=image)

    # determine target image size based on padding mode
    if padding_mode is None:
        # no padding
        target_size = image_size
    elif padding_mode == "tight":
        # tight padding: pad the image such that the given rotation exactly fits in
        angle_rad = angle_deg * np.pi / 180.0
        sin_angle = np.abs(np.sin(angle_rad))
        cos_angle = np.abs(np.cos(angle_rad))
        target_size = (
            int(np.ceil(cos_angle * image_size[0] + sin_angle * image_size[1])),
            int(np.ceil(cos_angle * image_size[1] + sin_angle * image_size[0])),
        )
    elif padding_mode == "full":
        # full padding: pad the image such that any rotation would fit in
        diag = int(np.ceil(np.sqrt(image_size[0]**2 + image_size[1]**2)))
        target_size = (diag, diag)
    else:
        raise ValueError("Invalid padding mode '{}'".format(padding_mode))

    # get rotation matrix and change the translation to match the target image size
    rotation_matrix = cv2.getRotationMatrix2D(center=(image.shape[1] // 2, image.shape[0] // 2), angle=angle_deg, scale=1.0)
    rotation_matrix[0, 2] += target_size[0] // 2 - image_size[0] // 2
    rotation_matrix[1, 2] += target_size[1] // 2 - image_size[1] // 2

    return cv2.warpAffine(src=image, M=rotation_matrix, dsize=target_size, flags=interpolation)


def rotate_90(image):
    """
    Rotate the given `image` by 90 degrees counterclockwise.

    Parameters
    ----------
    image : np.ndarray
        Input image to be rotated.

    Returns
    -------
    np.ndarray
        Rotated image.

    See Also
    --------
    cv2.rotate : Function that performs the image rotation.
    """
    return cv2.rotate(src=image, rotateCode=cv2.ROTATE_90_COUNTERCLOCKWISE)


def rotate_180(image):
    """
    Rotate the given `image` by 180 degrees.

    Parameters
    ----------
    image : np.ndarray
        Input image to be rotated.

    Returns
    -------
    np.ndarray
        Rotated image.

    See Also
    --------
    cv2.rotate : Function that performs the image rotation.
    """
    return cv2.rotate(src=image, rotateCode=cv2.ROTATE_180)


def rotate_270(image):
    """
    Rotate the given `image` by 270 degrees counterclockwise (= 90 degrees clockwise).

    Parameters
    ----------
    image : np.ndarray
        Input image to be rotated.

    Returns
    -------
    np.ndarray
        Rotated image.

    See Also
    --------
    cv2.rotate : Function that performs the image rotation.
    """
    return cv2.rotate(src=image, rotateCode=cv2.ROTATE_90_CLOCKWISE)


def warp_affine(image, angle_deg=0.0, scale=1.0, tx=0.0, ty=0.0, interpolation=cv2.INTER_LINEAR, border_mode=cv2.BORDER_REFLECT_101, border_value=0):
    """
    Apply an affine transformation to the given `image`, including rotation, scaling, and translation.

    Parameters
    ----------
    image : np.ndarray
        Input image to be transformed.
    angle_deg : float, optional
        Rotation angle in degrees. Default is 0.0.
    scale : float, optional
        Scaling factor. A value greater than 1.0 enlarges the image content, while a value less than 1.0 shrinks it.
        Note: the resulting image shape is the same as the input image shape in either case.
        Default is 1.0.
    tx : float, optional
        Horizontal translation (shift) in pixels. Positive values move the image to the right,
        and negative values move it to the left. Default is 0.0.
    ty : float, optional
        Vertical translation (shift) in pixels. Positive values move the image downwards,
        and negative values move it upwards. Default is 0.0.
    interpolation : int, optional
        Interpolation method to use. See `cv2.warpAffine()` for valid options.
        Defaults to `cv2.INTER_LINEAR`.
    border_mode : int, optional
        Pixel extrapolation method when the image is transformed out of bounds. See `cv2.warpAffine()` for options.
        Defaults to `cv2.BORDER_REFLECT_101`.
    border_value : int, optional
        Value used in case of a constant border. Default is 0.

    Returns
    -------
    np.ndarray
        Transformed image.

    See Also
    --------
    cv2.getRotationMatrix2D : Function to get the 2D rotation and scaling matrix.
    cv2.warpAffine : Function that performs the affine transformation.
    """

    image_size = size(image=image)

    rotation_matrix = cv2.getRotationMatrix2D(center=(image.shape[1] // 2, image.shape[0] // 2), angle=angle_deg, scale=scale)
    rotation_matrix[0, 2] += tx
    rotation_matrix[1, 2] += ty

    return cv2.warpAffine(src=image, M=rotation_matrix, dsize=image_size, flags=interpolation, borderMode=border_mode, borderValue=border_value)


#
# channel-related
#
    

def is_gray(image):
    """
    Check if the given `image` is a valid grayscale image.

    Here, 'valid grayscale image' means that it has either two dimensions, or three dimensions with the last one being
    singleton.

    Parameters
    ----------
    image : np.ndarray
        The image to check.

    Returns
    -------
    bool
        True if the image is grayscale, False otherwise.
    """
    
    return (len(image.shape) == 2) or ((len(image.shape) == 3) and (image.shape[2] == 1))


def is_color(image):
    """
    Check if the given `image` is a valid color image.

    Here, 'valid color image' means that it has three dimensions, with the last dimension having a length of three (the
    color channels).

    Parameters
    ----------
    image : np.ndarray
        The image to check.

    Returns
    -------
    bool
        True if the image is color, False otherwise.
    """
    
    return (len(image.shape) == 3) and (image.shape[2] == 3)


def as_gray(image, keep_color_dimension=False):
    """
    Convert the given `image` from BGR to grayscale.

    If `image` is already a grayscale image, return it unchanged.

    Parameters
    ----------
    image : np.ndarray
        The input image to be converted to grayscale.
    keep_color_dimension : bool, optional
        If True, the output grayscale image will have a shape of `(height, width, 1)`. If False (default), the output
        image will have a shape of `(height, width)`.

    Returns
    -------
    np.ndarray
        Grayscale image.

    See Also
    --------
    is_gray : Check if an image is grayscale.
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """

    if is_gray(image=image):
        image_gray = image
    else:
        image_gray = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2GRAY)

    if keep_color_dimension and (len(image_gray.shape) == 2):
        image_gray = image_gray[:, :, np.newaxis]

    return image_gray


def as_color(image):
    """
    Convert the given `image` from grayscale to BGR.

    If `image` is already a color image, return it unchanged.

    Parameters
    ----------
    image : np.ndarray
        The input image to be converted to BGR.

    Returns
    -------
    np.ndarray
        BGR color image.

    See Also
    --------
    is_color : Check if an image is color.
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """
    
    if is_color(image=image):
        return image
    else:
        return cv2.cvtColor(src=image, code=cv2.COLOR_GRAY2BGR)


def convert_color(image_or_color, code):
    """
    Convert the given `image_or_color` from one color space to another.

    This function supports both images and color tuples and returns an image or a color tuple depending on the input.

    Parameters
    ----------
    image_or_color : np.ndarray or tuple
        The image or color to be converted.
    code : int
        The conversion code that specifies the target color space as required by `cv2.cvtColor`.

    Returns
    -------
    np.ndarray or tuple
        The converted image or color.

    Raises
    ------
    ValueError
        If `image_or_color` is neither an image nor a color tuple.

    See Also
    --------
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """

    if isinstance(image_or_color, tuple) and (1 <= len(image_or_color) <= 3):
        # color mode
        color_array = np.array(image_or_color, dtype=np.uint8)
        color_array.shape = (1, 1, 3)
        return tuple(cv2.cvtColor(src=color_array, code=code)[0, 0, ...].tolist())
    elif dito.core.is_image(image_or_color):
        # image mode
        return cv2.cvtColor(src=image_or_color, code=code)
    else:
        raise ValueError("Argument 'image_or_color' must be an image or a color, but is '{}'".format(type(image_or_color)))


def bgr_to_hsv(image_or_color):
    """
    Convert the given `image_or_color` from BGR to HSV color space.

    Parameters
    ----------
    image_or_color : np.ndarray or tuple
        The image or color to be converted.

    Returns
    -------
    np.ndarray or tuple
        The converted image or color in HSV color space.

    See Also
    --------
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """
    return convert_color(image_or_color=image_or_color, code=cv2.COLOR_BGR2HSV)


def hsv_to_bgr(image_or_color):
    """
    Convert the given `image_or_color` from HSV to BGR color space.

    Parameters
    ----------
    image_or_color : np.ndarray or tuple
        The image or color to be converted.

    Returns
    -------
    np.ndarray or tuple
        The converted image or color in BGR color space.

    See Also
    --------
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """
    return convert_color(image_or_color=image_or_color, code=cv2.COLOR_HSV2BGR)


def flip_channels(image):
    """
    Flip the color channels of the given `image` from BGR to RGB and vice versa.

    If the input image is in BGR format (the default when using OpenCV), it is converted to RGB format.
    If it is in RGB format, it is converted to BGR.

    Parameters
    ----------
    image : np.ndarray
        Input image in either BGR or RGB format.

    Returns
    -------
    np.ndarray
        Output image in the flipped color format.

    See Also
    --------
    cv2.cvtColor : OpenCV function that performs the color conversion.
    """
    return cv2.cvtColor(src=image, code=cv2.COLOR_BGR2RGB)


def split_channels(image):
    """
    Split the given image into a tuple containing its channels as individual images.

    If the `image` has no color dimension, return a singleton tuple.

    Parameters
    ----------
    image : np.ndarray
        The image to split.

    Returns
    -------
    tuple of np.ndarray
        A tuple containing the individual channels of the input image.

    Raises
    ------
    dito.exceptions.InvalidImageShapeError
        If the input image shape does not have two or three axes.
    """
    axis_count = len(image.shape)
    if axis_count == 2:
        return (image,)
    elif axis_count == 3:
        return tuple(image[:, :, n_channel] for n_channel in range(image.shape[2]))
    else:
        raise dito.exceptions.InvalidImageShapeError("Image shape must have two or three axes, but is {}".format(image.shape))


def as_channels(b=None, g=None, r=None):
    """
    Merge up to three grayscale images into one color image.

    Each of the input images will be assigned to a specific (BGR) color channel in the output image.
    If an input image is not provided for a color channel, that channel will be filled with zeros.

    Parameters
    ----------
    b : np.ndarray or None, optional
        The image to use for the blue color channel.
    g : np.ndarray or None, optional
        The image to use for the green color channel.
    r : np.ndarray or None, optional
        The image to use for the red color channel.

    Returns
    -------
    np.ndarray
        The BGR color image created by merging the input images.

    Raises
    ------
    ValueError
        If none of the input arguments is provided.

        If an input image is not grayscale.

        If the input images have different shapes.

    See Also
    --------
    cv2.merge : OpenCV function that performs the merging.
    """
    # check arguments
    if (b is None) and (g is None) and (r is None):
        raise ValueError("At least for one channel an image must be given")

    # get the first non-`None` image (needed to determine the shape and dtype below)
    for channel_image in (b, g, r):
        if channel_image is not None:
            channel_image_zero = 0 * channel_image
            break

    channel_images = []
    for channel_image in (b, g, r):
        if channel_image is not None:
            if not is_gray(image=channel_image):
                raise ValueError("At least one of the given images is not a gray scale image")
            channel_images.append(channel_image)
        else:
            channel_images.append(channel_image_zero)

    return cv2.merge(mv=channel_images)


#
# value-related
#


def clip(image, lower=None, upper=None):
    """
    Clip values of the given `image` to the range specified by `lower` and `upper`.

    Parameters
    ----------
    image : np.ndarray
        The input image.
    lower : float or int or None
        Lower bound of the clipping range (inclusive). If `None`, no lower bound is applied.
    upper : float or int or None
        Upper bound of the clipping range (inclusive). If `None`, no upper bound is applied.

    Returns
    -------
    np.ndarray
        Clipped image.

    Notes
    -----
    This function makes a copy of the input array to avoid modifying it in place.

    Examples
    --------
    >>> clip(image=np.arange(10, dtype=np.uint8)[np.newaxis, :], lower=2, upper=6)
    array([[2, 2, 2, 3, 4, 5, 6, 6, 6, 6]], dtype=uint8)
    """

    # assert that the input array remains unchanged
    image = image.copy()

    # clip
    if lower is not None:
        image[image < lower] = lower
    if upper is not None:
        image[image > upper] = upper

    return image


def clip_01(image):
    """
    Clip values of the given `image` to the range `(0.0, 1.0)`.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    np.ndarray
        Clipped image with values in the range `(0.0, 1.0)`.

    Examples
    --------
    >>> clip_01(image=np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32))
    array([[0., 0., 0., 1., 1.]], dtype=float32)
    """
    return clip(image=image, lower=0.0, upper=1.0)


def clip_11(image):
    """
    Clip values of the given `image` to the range `(-1.0, 1.0)`.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    np.ndarray
        Clipped image with values in the range `(-1.0, 1.0)`.

    Examples
    --------
    >>> clip_11(image=np.array([[-2.0, -1.0, 0.0, 1.0, 2.0]], dtype=np.float32))
    array([[-1., -1.,  0.,  1.,  1.]], dtype=float32)
    """
    return clip(image=image, lower=-1.0, upper=1.0)


def clip_0255(image):
    """
    Clip values of the given `image` to the range `(0.0, 255.0)`.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    np.ndarray
        Clipped image with values in the range `(0.0, 255.0)`.

    Examples
    --------
    >>> clip_0255(image=np.array([[-1.0, 0.0, 1.0, 255.0, 300.0]], dtype=np.float32))
    array([[  0.,   0.,   1., 255., 255.]], dtype=float32)
    """
    return clip(image=image, lower=0.0, upper=255.0)


def normalize(image, mode="minmax", **kwargs):
    """
    Normalize the intensity values of the given `image` to a certain range.

    The supported normalization modes are:
      - 'none': do not normalize the image
      - 'interval': rescale the image intensity values from a specified interval (kwargs `lower` and `upper`) to the full data type range of the image
      - 'minmax': rescale the image intensity values to the full data type range of the image, using the minimum and maximum values
      - 'zminmax': means 'zero-symmetric minmax', i.e., rescale the image intensity values to (-`extreme_value`, `extreme_value`), where `extreme_value` is the largest absolute value of the image
      - 'percentile': rescale the image intensity values to the full data type range of the image, using the given percentiles

    Parameters
    ----------
    image : np.ndarray
        Input image to be normalized.
    mode : str, optional
        Normalization mode. Valid modes are {'none', 'interval', 'minmax', 'zminmax', 'percentile'}.
    **kwargs
        Additional keyword arguments specific to each mode. See Notes section for more details.

    Returns
    -------
    np.ndarray
        The normalized image.

    Raises
    ------
    ValueError
        If an invalid normalization mode is given.

    Notes
    -----
    The additional keyword arguments (`**kwargs`) that are specific to each normalization mode are:

      - 'none': no additional keyword arguments are used
      - 'interval': the following arguments are required:
        - 'lower' (float or int): lower bound of the source interval
        - 'upper' (float or int): upper bound of the source interval
      - 'minmax': no additional keyword arguments are used
      - 'zminmax': no additional keyword arguments are used
      - 'percentile': the following arguments are optional:
        - 'q' or 'p' (float): percentile to be used for lower and upper bounds (default: 2.0)
    """

    if mode == "none":
        return image

    elif mode == "interval":
        # interval range to be spread out to the "full" interval range
        (lower_source, upper_source) = sorted((kwargs["lower"], kwargs["upper"]))

        # the target interval range depends on the image's data type
        (lower_target, upper_target) = dtype_range(image.dtype)

        # we temporarily work with a float image (because values outside the target interval can occur)
        image_work = image.astype("float").copy()
        
        # spread the given interval to the full range, clip outlier values
        image_work = (image_work - lower_source) / (upper_source - lower_source) * (upper_target - lower_target) + lower_target
        image_work = clip(image=image_work, lower=lower_target, upper=upper_target)

        # return an image with the original data type
        return image_work.astype(image.dtype)

    elif mode == "minmax":
        return normalize(image, mode="interval", lower=np.min(image), upper=np.max(image))

    elif mode == "zminmax":
        # "zero-symmetric" minmax (makes only sense for float images)
        absmax = max(np.abs(np.min(image)), np.abs(np.max(image)))
        return normalize(image, mode="interval", lower=-absmax, upper=absmax)

    elif mode == "percentile":
        for key in ("q", "p"):
            if key in kwargs.keys():
                q = kwargs[key]
                break
        else:
            q = 2.0
        q = min(max(0.0, q), 50.0)
        return normalize(image, mode="interval", lower=np.percentile(image, q), upper=np.percentile(image, 100.0 - q))

    else:
        raise ValueError("Invalid mode '{mode}'".format(mode=mode))


def invert(image):
    """
    Invert the intensity values of the given image.

    Parameters
    ----------
    image : np.ndarray
        The image to invert.

    Returns
    -------
    np.ndarray
        The inverted image.

    Raises
    ------
    ValueError
        If the image has an unsupported data type or a minimum value other than 0.0.

    Examples
    --------
    >>> invert(image=np.array([[0, 100, 200, 255]], dtype=np.uint8))
    array([[255, 155,  55,   0]], dtype=uint8)

    >>> invert(image=np.array([[0.0, 0.25, 0.5, 1.0]], dtype=np.float32))
    array([[1.  , 0.75, 0.5 , 0.  ]], dtype=float32)

    >>> invert(image=np.array([[False, True]], dtype=bool))
    array([[ True, False]])
    """

    if is_integer_image(image=image) or is_float_image(image=image):
        image_dtype_range = dtype_range(dtype=image.dtype)
        if float(image_dtype_range[0]) != 0.0:
            raise ValueError("Argument 'image' must have dtype with min value of zero (but has dtype '{}')".format(image.dtype))
        return image_dtype_range[1] - image

    elif is_bool_image(image=image):
        return np.logical_not(image)

    else:
        raise ValueError("Unsupported image dtype '{}'".format(image.dtype))
