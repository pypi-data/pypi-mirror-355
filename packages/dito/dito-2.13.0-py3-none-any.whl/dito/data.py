"""
This submodule provides functionality to generate and load images with specific properties.
"""

import os.path
import random

import cv2
import numpy as np

import dito.io


#
# resource filenames
#


RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
RESOURCES_FILENAMES = {
    # colormaps (self-defined)
    "colormap:plot": os.path.join(RESOURCES_DIR, "colormaps", "plot.png"),
    "colormap:plot2": os.path.join(RESOURCES_DIR, "colormaps", "plot2.png"),

    # colorbrewer colormaps (note: this product includes color specifications and designs developed by Cynthia Brewer (http://colorbrewer.org/).)
    "colormap:accent": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "accent.png"),
    "colormap:blues": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "blues.png"),
    "colormap:brbg": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "brbg.png"),
    "colormap:bugn": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "bugn.png"),
    "colormap:bupu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "bupu.png"),
    "colormap:dark2": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "dark2.png"),
    "colormap:gnbu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "gnbu.png"),
    "colormap:greens": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "greens.png"),
    "colormap:greys": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "greys.png"),
    "colormap:orrd": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "orrd.png"),
    "colormap:oranges": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "oranges.png"),
    "colormap:prgn": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "prgn.png"),
    "colormap:paired": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "paired.png"),
    "colormap:pastel1": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "pastel1.png"),
    "colormap:pastel2": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "pastel2.png"),
    "colormap:piyg": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "piyg.png"),
    "colormap:pubu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "pubu.png"),
    "colormap:pubugn": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "pubugn.png"),
    "colormap:puor": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "puor.png"),
    "colormap:purd": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "purd.png"),
    "colormap:purples": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "purples.png"),
    "colormap:rdbu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "rdbu.png"),
    "colormap:rdgy": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "rdgy.png"),
    "colormap:rdpu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "rdpu.png"),
    "colormap:rdylbu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "rdylbu.png"),
    "colormap:rdylgn": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "rdylgn.png"),
    "colormap:reds": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "reds.png"),
    "colormap:set1": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "set1.png"),
    "colormap:set2": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "set2.png"),
    "colormap:set3": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "set3.png"),
    "colormap:spectral": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "spectral.png"),
    "colormap:ylgn": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "ylgn.png"),
    "colormap:ylgnbu": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "ylgnbu.png"),
    "colormap:ylorbr": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "ylorbr.png"),
    "colormap:ylorrd": os.path.join(RESOURCES_DIR, "colormaps", "colorbrewer", "ylorrd.png"),

    # fonts: Scientifica
    "font:scientifica-12": os.path.join(RESOURCES_DIR, "fonts", "scientifica", "scientifica_df2.png"),

    # font: Source Code Pro
    "font:source-10": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "10_df2.png"),
    "font:source-15": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "15_df2.png"),
    "font:source-20": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "20_df2.png"),
    "font:source-25": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "25_df2.png"),
    "font:source-30": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "30_df2.png"),
    "font:source-35": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "35_df2.png"),
    "font:source-40": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "40_df2.png"),
    "font:source-50": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "50_df2.png"),
    "font:source-70": os.path.join(RESOURCES_DIR, "fonts", "source_code_pro", "70_df2.png"),

    # font: Terminus
    "font:terminus-12": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u12_df2.png"),
    "font:terminus-14": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u14_df2.png"),
    "font:terminus-16": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u16_df2.png"),
    "font:terminus-18": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u18_df2.png"),
    "font:terminus-20": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u20_df2.png"),
    "font:terminus-22": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u22_df2.png"),
    "font:terminus-24": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u24_df2.png"),
    "font:terminus-28": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u28_df2.png"),
    "font:terminus-32": os.path.join(RESOURCES_DIR, "fonts", "terminus", "ter-u32_df2.png"),

    # test images
    "image:PM5544": os.path.join(RESOURCES_DIR, "images", "PM5544.png"),
    "image:USC-SIPI-4.1.07": os.path.join(RESOURCES_DIR, "images", "USC_SIPI_4.1.07.png"),
}


#
# synthetic images
#


def constant_image(size=(512, 288), color=(0, 255, 0), dtype=np.uint8):
    """
    Return an image where all pixels have the same color.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the output image. Default is (512, 288).
    color : tuple of int, optional
        The color of the image as a tuple of values for each color channel. Default is (0, 255, 0).
    dtype : data-type, optional
        The desired data type of the output image. Default is np.uint8.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    channel_count = len(color)
    image = np.zeros(shape=(size[1], size[0], channel_count), dtype=dtype)
    for n_channel in range(channel_count):
        image[:, :, n_channel] = color[n_channel]
    if channel_count == 1:
        image = image[:, :, 0]
    return image


def grid(size=(512, 288), grid_size=16, background_color=(0,), grid_color=(255,), offset=None, dtype=np.uint8):
    """
    Return an image of the given `size` containing regular grid lines.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the output image. Default is (512, 288).
    grid_size : int, optional
        The size of the grid blocks. Default is 16.
    background_color : tuple of int, optional
        The background color of the image. Default is (0,).
    grid_color : tuple of int, optional
        The color of the grid lines. Default is (255,).
    offset : tuple of int, optional
        The offset of the grid lines from the top-left corner of the image. Default is None.
    dtype : data-type, optional
        The desired data type of the output image. Default is np.uint8.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    image = constant_image(size=size, color=background_color, dtype=dtype)

    if offset is None:
        offset = (0, 0)
    else:
        offset = dito.utils.get_validated_tuple(x=offset, type_=int, count=2, min_value=0)

    for x in range(offset[0] % grid_size, size[0], grid_size):
        image[:, x, ...] = grid_color

    for y in range(offset[1] % grid_size, size[1], grid_size):
        image[y, :, ...] = grid_color

    return image


def checkerboard(size=(512, 288), block_size=16, low=0, high=255):
    """
    Return a grayscale image of the given `size` containing a checkerboard grid.

    The arguments `low` and `high` specify the gray scale values to be used for the squares.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the output image. Default is (512, 288).
    block_size : int, optional
        The size of the checkerboard squares. Default is 16.
    low : int, optional
        The grayscale value of the low intensity squares. Default is 0.
    high : int, optional
        The grayscale value of the high intensity squares. Default is 255.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    image = np.zeros(shape=(size[1], size[0]), dtype=np.uint8) + low
    for (n_row, y) in enumerate(range(0, size[1], block_size)):
        offset = block_size if ((n_row % 2) == 0) else 0
        for x in range(offset, size[0], 2 * block_size):
            image[y:(y + block_size), x:(x + block_size)] = high

    return image


def background_checkerboard(size=(512, 288), block_size=16):
    """
    Return a grayscale image of the given `size` containing a checkerboard grid of light and dark gray squares.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the output image. Default is (512, 288).
    block_size : int, optional
        The size of the checkerboard squares. Default is 16.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    return checkerboard(size=size, block_size=block_size, low=80, high=120)


def xslope(height=32, width=256, dtype=np.uint8):
    """
    Return a grayscale image containing values increasing from 0 to 255 along the x axis.

    For dtypes other than uint8, the values range from

    Parameters
    ----------
    height : int, optional
        The height of the output image. Default is 32.
    width : int, optional
        The width of the output image. Default is 256.
    dtype : data-type, optional
        The desired data type of the output image. Default is np.uint8.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    dtype_range = dito.core.dtype_range(dtype=dtype)
    slope = np.linspace(start=dtype_range[0], stop=dtype_range[1], num=width, endpoint=True, dtype=dtype)
    slope.shape = (1,) + slope.shape
    slope = np.repeat(a=slope, repeats=height, axis=0)
    return slope


def yslope(width=32, height=256, dtype=np.uint8):
    """
    Return a grayscale image containing values increasing from 0 to 255 along the y axis.

    Parameters
    ----------
    width : int, optional
        The width of the output image. Default is 32.
    height : int, optional
        The height of the output image. Default is 256.
    dtype : data-type, optional
        The desired data type of the output image. Default is np.uint8.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    return xslope(height=width, width=height, dtype=dtype).T


def random_image(size=(512, 288), color=True, dtype=np.uint8, use_standard_library=False):
    """
    Return a random image of the given `size` and `dtype`.

    The values will span the full range of the specified dtype.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the output image. Default is (512, 288).
    color : bool, optional
        If True, the image will have 3 channels representing BGR. Otherwise, it will be grayscale. Default is True.
    dtype : data-type, optional
        The desired data type of the output image. Default is np.uint8.
    use_standard_library : bool, optional
        If True, the random values will be generated using the Python standard library's `random` module. Otherwise,
        NumPy's `np.random.rand()` function will be used. Default is False.

    Returns
    -------
    numpy.ndarray
        The output image.
    """
    shape = tuple(size[::-1])
    if color:
        shape = shape + (3,)

    if use_standard_library:
        image_random = np.array([random.random() for _ in range(np.prod(shape))], dtype=np.float32).reshape(*shape)
    else:
        image_random = np.random.rand(*shape)

    return dito.core.convert(image=image_random, dtype=dtype)


def test_image_segments():
    """
    Create a test image with segments of circles, squares, ellipses and rectangles.

    The image has a size of (512, 288) and is of data type uint8.

    Returns
    -------
    numpy.ndarray
        A 2D NumPy array representing the image.
    """
    image = np.zeros(shape=(288, 512), dtype=np.uint8)

    sep = 8
    count = 10
    radii = [round(2**(2 + n_circle / 4)) for n_circle in range(count)]
    color = (255,)

    # draw series of circles
    center_x = sep + max(radii)
    center_y = sep
    for radius in radii:
        center_y += radius
        cv2.circle(img=image, center=(center_x, center_y), radius=radius, color=color, thickness=cv2.FILLED, lineType=cv2.LINE_8)
        center_y += radius + sep

    # draw series of squares
    center_x = 2 * sep + 3 * max(radii)
    center_y = sep
    for radius in radii:
        center_y += radius
        cv2.rectangle(img=image, pt1=dito.core.tir(center_x - radius, center_y - radius), pt2=dito.core.tir(center_x + radius, center_y + radius), color=color, thickness=cv2.FILLED, lineType=cv2.LINE_8)
        center_y += radius + sep

    # draw series of ellipses
    center_x = 3 * sep + 6 * max(radii)
    center_y = sep
    for radius in radii:
        center_y += radius
        cv2.ellipse(img=image, center=(center_x, center_y), axes=(radius * 2, radius), angle=0.0, startAngle=0.0, endAngle=360.0, color=color, thickness=cv2.FILLED, lineType=cv2.LINE_8)
        center_y += radius + sep

    # draw series of rectangles
    center_x = 4 * sep + 10 * max(radii)
    center_y = sep
    for radius in radii:
        center_y += radius
        cv2.rectangle(img=image, pt1=dito.core.tir(center_x - radius * 2, center_y - radius), pt2=dito.core.tir(center_x + radius * 2, center_y + radius), color=color, thickness=cv2.FILLED, lineType=cv2.LINE_8)
        center_y += radius + sep

    return image


class DitoTestImageGeneratorV1():
    """
    Class which is used to generate test input images for processing functions.

    Depending on the specified image size, the selection and count of the elements may change.

    The generated images feature the following elements:
    * background color slope for absolute image position/crop assessment
    * grid for assessment of deformations
    * corner indicators for image flip/reflection assessment
    * pixel ruler for length measurements
    * crosshair for image center localization
    * gray slopes for gamma measurements
    * color areas for channel order assessment
    * random color areas for assessment of random seed values of the `random` module and for NumPy.
    * lines with different inclinations for rotation assessment
    * letters/numbers for text appearance assessment

    TODO:
    * checkerboard patterns with different resolutions
    * lines with different widths/separations for resolution measurements
    * OpenCV checkerboard pattern for possible automated detection
    * color wheel for color mapping assessment

    Attributes
    ----------
    image : numpy.ndarray
        The generated image.
    """

    def __init__(self, size, dtype):
        """
        Create an instance of the class `DitoTestImageGeneratorV1`.

        Parameters
        ----------
        size : tuple
            The size (width, height) of the image to be generated.
        dtype : dtype
            The data type of the image to be generated.
        """

        # settings
        self.grid_size = 16
        self.ruler_size = 16
        self.line_color = (240, 240, 240)

        # arguments
        self.size = size
        self.dtype = dtype

        # checks
        if min(self.size) < 2 * self.grid_size:
            raise RuntimeError("Size '{}' is too small".format(self.size))
        assert (self.dtype in (np.uint8, np.uint16)) or dito.core.is_float_dtype(dtype=self.dtype)

        # derived properties
        self.size_min = min(self.size)
        self.image_center = (self.size[0] // 2, self.size[1] // 2)
        self.dtype_range = dito.core.dtype_range(dtype=self.dtype)
        (self.grid_offset, self.grid_inner_offset, self.grid_inner_count) = self.calculate_grid_parameters()
        self.min_inner_count = min(self.grid_inner_count)
        self.max_inner_count = max(self.grid_inner_count)

        # image construction
        self.image = self.generate_base_image()
        if self.min_inner_count >= 2:
            self.draw_corner_identifier_texts()
        if self.min_inner_count >= 2:
            self.draw_rulers()
        if self.max_inner_count >= 4:
            self.draw_center_crosshair()
        if self.min_inner_count >= 4:
            self.draw_gray_slopes()
        if self.min_inner_count >= 6:
            self.draw_color_areas()
        if self.min_inner_count >= 8:
            self.draw_rotation_indicators()
            #self.draw_checkerboard_patterns()

    def adapt_color_for_dtype(self, color):
        """
        Internal helper function.

        Map an `numpy.uint8` color (range `[0, 255]`) to the correct range of
        the dtype of this image.

        Parameters
        ----------
        color : int or tuple of ints

        Returns
        -------
        int or tuple of
        """
        try:
            len(color)
        except TypeError:
            # color is a scalar
            return_scalar = True
            color = (color,)
        else:
            # color is vector-like
            return_scalar = False

        if self.dtype == np.uint8:
            pass
        elif self.dtype == np.uint16:
            color = tuple(value * 257 for value in color)
        elif dito.core.is_float_dtype(dtype=self.dtype):
            color = tuple(value / 255.0 for value in color)
        else:
            raise TypeError("Invalid dtype '{}'".format(self.dtype))

        if return_scalar:
            assert len(color) == 1
            return color[0]
        else:
            return color

    def calculate_grid_parameters(self):
        """
        Internal helper function.

        Calculate offsets and other related properties of the grid to be drawn into the image.

        Returns
        -------
        tuple of tuples of ints
            Grid properties (grid offset, inner grid offset, inner grid count).
        """
        grid_offset = [(self.size[n_dim] % (2 * self.grid_size)) // 2 for n_dim in range(2)]
        grid_inner_offset = [grid_offset[n_dim] + self.grid_size if self.ruler_size > grid_offset[n_dim] else grid_offset[n_dim] for n_dim in range(2)]
        grid_inner_count = [(self.size[n_dim] - 2 * grid_offset[n_dim]) // self.grid_size - 2 if self.ruler_size > grid_offset[n_dim] else (self.size[n_dim] - 2 * grid_offset[n_dim]) // self.grid_size for n_dim in range(2)]
        return (grid_offset, grid_inner_offset, grid_inner_count)

    def get_grid_coords(self, index_x, index_y):
        """
        Internal helper function.

        Map grid coordinates `(index_x, index_y)` to image pixel coordinates `(x, y)`.

        Parameters
        ----------
        index_x : int
            Grid x coordinate.
        index_y : int
            Grid y coordinate.

        Returns
        -------
        tuple of int
            Point `(x, y)` in image coordinates.

        Note
        ----
        Negative values wrap around from the end, just like for normal indexing.
        """
        if index_x < 0:
            index_x = index_x % self.grid_inner_count[0]
        if index_y < 0:
            index_y = index_y % self.grid_inner_count[1]
        return [self.grid_inner_offset[n_dim] + [index_x, index_y][n_dim] * self.grid_size for n_dim in range(2)]

    def generate_base_image(self):
        """
        Internal helper function.

        Generate the base of the test image to be created. It contains slopes
        in the blue (along the y axis) and green (along the x axis) channels,
        and a regular grid in the red channel.

        Returns
        -------
        numpy.ndimage
            The base image.
        """
        image_x = xslope(height=self.size[1], width=self.size[0], dtype=self.dtype)
        image_y = yslope(height=self.size[1], width=self.size[0], dtype=self.dtype)

        image_grid = None
        for n_grid_level in range(4):
            image_grid_level = grid(size=self.size, grid_size=self.grid_size // (2**n_grid_level), background_color=(0,), grid_color=self.adapt_color_for_dtype((2**(8 - n_grid_level) - 1,)), offset=self.grid_offset, dtype=self.dtype)
            if image_grid is None:
                image_grid = image_grid_level
            else:
                image_grid = np.maximum(image_grid, image_grid_level)

        image = dito.core.as_channels(b=image_y, g=image_x, r=image_grid)
        return image

    def draw_center_crosshair(self):
        """
        Internal helper function.

        Draw a crosshair at the center of the test image `self.image`.

        Returns
        -------
        None
        """
        for radius in (0, 2, 5, 9, 14):
            dito.draw.draw_symbol(image=self.image, symbol="square", position=self.image_center, radius=radius, color=self.adapt_color_for_dtype(self.line_color), thickness=1, line_type=cv2.LINE_8)

    def draw_rulers(self):
        """
        Internal helper function.

        Draw rulers into the test image `self.image`.

        Returns
        -------
        None
        """
        for n_dim in range(2):
            for n_index in range(0, self.image.shape[n_dim], 2):
                for n_channel in range(3):
                    indices = [None, None, n_channel]
                    indices[n_dim] = n_index
                    indices[2] = n_channel
                    n_index_corrected = (n_index // 2) % self.ruler_size
                    index = 2 * min(n_index_corrected, self.ruler_size - n_index_corrected) + 1
                    indices[1 - n_dim] = slice(None, index)
                    self.image[tuple(indices)] = self.adapt_color_for_dtype(self.line_color[n_channel])
                    indices[1 - n_dim] = slice(min(-1, -index + 1), None)
                    self.image[tuple(indices)] = self.adapt_color_for_dtype(self.line_color[n_channel])

    def draw_corner_identifier_texts(self):
        """
        Internal helper function.

        Draw corner identifiers into the test image `self.image`.

        Returns
        -------
        None
        """
        text_kwargs = {"anchor": "lt", "font": "terminus-14", "style": "bold", "background_color": None, "background_as_outline": False}
        (text_x_left, text_y_top) = [int(coord + 1) for coord in self.get_grid_coords(0, 0)]
        (text_x_right, text_y_bottom) = [int(coord + 1) for coord in self.get_grid_coords(-1, -1)]
        self.image = dito.visual.text(image=self.image, message="TL", position=(text_x_left, text_y_top), **text_kwargs)
        self.image = dito.visual.text(image=self.image, message="TR", position=(text_x_right, text_y_top), **text_kwargs)
        self.image = dito.visual.text(image=self.image, message="BL", position=(text_x_left, text_y_bottom), **text_kwargs)
        self.image = dito.visual.text(image=self.image, message="BR", position=(text_x_right, text_y_bottom), **text_kwargs)

    def draw_gray_slopes(self):
        """
        Internal helper function.

        Draw gray scale slopes into the test image `self.image`.

        Returns
        -------
        None
        """

        slopes = [
            {"coord_offset_from": (1, 0), "coord_offset_to": (-1, 1), "direction": "lr"},
            {"coord_offset_from": (1, -1), "coord_offset_to": (-1, self.grid_inner_count[1]), "direction": "rl"},
            {"coord_offset_from": (0, 1), "coord_offset_to": (1, -1), "direction": "ud"},
            {"coord_offset_from": (-1, 1), "coord_offset_to": (self.grid_inner_count[0], -1), "direction": "du"},
        ]

        for slope in slopes:
            (x_from, y_from) = self.get_grid_coords(*slope["coord_offset_from"])
            (x_to, y_to) = self.get_grid_coords(*slope["coord_offset_to"])
            if slope["direction"] in ("lr", "rl"):
                slope_image = xslope(height=self.grid_size - 1, width=abs(x_from - x_to), dtype=self.dtype)
                slope_image = dito.core.as_color(image=slope_image)
                if slope["direction"] == "lr":
                    slope_image = slope_image[:, ::-1, ...].copy()
                    slope_image = dito.core.resize(dito.core.resize(slope_image, 1.0 / self.grid_size), dito.core.size(slope_image))
                    for n_col in range(slope_image.shape[1] // self.grid_size):
                        (text_x, text_y) = dito.core.tir((n_col + 0.5) * self.grid_size, self.grid_size // 2)
                        slope_image = dito.visual.text(image=slope_image, message=str(n_col % 100 + 1), position=(text_x, text_y), anchor="cc", font="terminus-12", color=dito.visual.max_distant_color(color=slope_image[text_y, text_x, :]), background_color=None)
                self.image[(y_from + 1):y_to, (x_from + 1):(x_to + 1), :] = slope_image
            else:
                slope_image = yslope(width=self.grid_size - 1, height=abs(y_from - y_to), dtype=self.dtype)
                slope_image = dito.core.as_color(image=slope_image)
                if slope["direction"] == "ud":
                    slope_image = slope_image[::-1, :, ...].copy()
                    slope_image = dito.core.resize(dito.core.resize(slope_image, 1.0 / self.grid_size), dito.core.size(slope_image))
                    for n_row in range(slope_image.shape[0] // self.grid_size):
                        (text_x, text_y) = dito.core.tir(self.grid_size // 2, (n_row + 0.5) * self.grid_size)
                        slope_image = dito.visual.text(image=slope_image, message=chr(ord("A") + n_row % 26), position=(text_x, text_y), anchor="cc", font="terminus-12", color=dito.visual.max_distant_color(color=slope_image[text_y, text_x, :]), background_color=None)
                self.image[(y_from + 1):(y_to + 1), (x_from + 1):x_to, :] = dito.core.as_color(image=slope_image)

    def draw_color_areas(self):
        """
        Internal helper function.

        Draw areas of fixed color into the test image `self.image`.

        Returns
        -------
        None
        """

        areas = [
            {"color": (255, 0, 0), "text_color": (0, 0, 0), "text": "B", "coord_offset": (-1, -2)},
            {"color": (255, 255, 0), "text_color": (0, 0, 0), "text": "C", "coord_offset": (0, -2)},
            {"color": (0, 255, 0), "text_color": (0, 0, 0), "text": "G", "coord_offset": (1, -1)},
            {"color": (0, 255, 255), "text_color": (0, 0, 0), "text": "Y", "coord_offset": (1, 0)},
            {"color": (0, 0, 255), "text_color": (0, 0, 0), "text": "R", "coord_offset": (0, 1)},
            {"color": (255, 0, 255), "text_color": (0, 0, 0), "text": "M", "coord_offset": (-1, 1)},
            {"color": (255, 255, 255), "text_color": (0, 0, 0), "text": "W", "coord_offset": (-2, 0)},
            {"color": (0, 0, 0), "text_color": (255, 255, 255), "text": "K", "coord_offset": (-2, -1)},
        ]
        for area in areas:
            (x, y) = self.get_grid_coords(self.grid_inner_count[0] // 2 + area["coord_offset"][0], self.grid_inner_count[1] // 2 + area["coord_offset"][1])
            self.image[(y + 1):(y + self.grid_size), (x + 1):(x + self.grid_size), ...] = self.adapt_color_for_dtype(area["color"])
            self.image = dito.text(image=self.image, message=area["text"], position=(x + self.grid_size // 2 + 1, y + self.grid_size // 2 + 1), anchor="cc", font="terminus-14", style="bold", color=area["text_color"], background_color=None)

        # random areas
        text_kwargs = {"anchor": "lt", "font": "terminus-14", "style": "bold", "background_color": None, "background_as_outline": False}
        for coord_offset_y in (-2, 1):
            if coord_offset_y == -2:
                color = (0, 0, 0)
            else:
                color = (255, 255, 255)

            # generated using the random module
            (x, y) = self.get_grid_coords(self.grid_inner_count[0] // 2 + coord_offset_y, self.grid_inner_count[1] // 2 - 2)
            self.image[(y + 1):(y + self.grid_size), (x + 1):(x + self.grid_size), ...] = random_image(size=(self.grid_size - 1, self.grid_size - 1), color=True, dtype=self.dtype, use_standard_library=True)
            self.image = dito.visual.text(image=self.image, message="S", position=(x + 1 + self.grid_size // 4, y + 1), color=color, **text_kwargs)

            # generated using NumPy
            (x, y) = self.get_grid_coords(self.grid_inner_count[0] // 2 + coord_offset_y,  self.grid_inner_count[1] // 2 + 1)
            self.image[(y + 1):(y + self.grid_size), (x + 1):(x + self.grid_size), ...] = random_image(size=(self.grid_size - 1, self.grid_size - 1), color=True, dtype=self.dtype, use_standard_library=False)
            self.image = dito.visual.text(image=self.image, message="N", position=(x + 1 + self.grid_size // 4, y + 2), color=color, **text_kwargs)

    def draw_rotation_indicators(self):
        """
        Internal helper function.

        Draw rotation indicators into the test image `self.image`.

        Returns
        -------
        None
        """
        for (n_resolution, resolution) in enumerate([5.0, 1.0]):
            sign = (-1)**n_resolution
            (x0, y0) = self.get_grid_coords(self.grid_inner_count[0] // 2, self.grid_inner_count[1] // 2 - 2 + 4 * n_resolution)
            y0 += -1 + 2 * n_resolution
            radius = (self.min_inner_count // 2 - 3) * self.grid_size - 2
            for n_angle in range(-9, 10):
                x_from = x0 + 4 * n_angle
                y_from = y0
                angle_deg = sign * resolution * n_angle
                angle_rad = angle_deg * np.pi / 180.0
                x_to = x_from + sign * radius * np.cos(angle_rad - np.pi * 0.5)
                y_to = y_from + sign * radius * np.sin(angle_rad - np.pi * 0.5)
                cv2.line(img=self.image, pt1=dito.core.tir(x_from, y_from), pt2=dito.core.tir(x_to, y_to), color=self.adapt_color_for_dtype(self.line_color), thickness=1, lineType=cv2.LINE_AA)

    def draw_checkerboard_patterns(self):
        """
        Internal helper function.

        Draw checkerboard patterns into the test image `self.image`.

        Returns
        -------
        None
        """
        for side in (0, 1):
            for (n_resolution, resolution) in enumerate([1, 3, 5, 7]):
                (x, y) = self.get_grid_coords(self.grid_inner_count[0] // 2 - 3 + 5 * side, self.grid_inner_count[1] // 2 - 2 + n_resolution)
                self.image[(y + 1):(y + self.grid_size), (x + 1):(x + self.grid_size), ...] = dito.core.as_color(checkerboard(size=(15, 15), block_size=resolution + side))


def dito_test_image_v1(size=(384, 256), dtype=np.uint8):
    """
    Wrapper function that returns a test image generated by the `DitoTestImageGeneratorV1` class.

    Parameters
    ----------
    size : tuple of int, optional
        The size (width, height) of the image to generate. Default is `(384, 256)`.
    dtype : data type, optional
        The data type of the image. Default is `numpy.uint8`.

    Returns
    -------
    numpy.ndarray
        The generated test image.

    See Also
    --------
    DitoTestImageGeneratorV1 : class used to generate the test image.
    """
    return DitoTestImageGeneratorV1(size=size, dtype=dtype).image


#
# real images
#


def pm5544():
    """
    Return image of the PM5544 test pattern.

    The image source (https://en.wikipedia.org/wiki/Philips_circle_pattern)
    states that this image is Public Domain.

    Returns
    -------
    numpy.ndarray, shape (576, 768, 3), dtype uint8
        The PM5544 test pattern image.
    """
    return dito.io.load(filename=RESOURCES_FILENAMES["image:PM5544"])


def usc_sipi_beans():
    """
    Returns the USC-SIPI database's image 4.1.07 ("Jelly beans").

    According to the copyright information under https://sipi.usc.edu/database/copyright.php,
    the image is free to use. Actual image source: http://sipi.usc.edu/database/database.php?volume=misc.

    Returns
    -------
    numpy.ndarray, shape (256, 256, 3), dtype uint8
        The jelly beans image.
    """
    return dito.io.load(filename=RESOURCES_FILENAMES["image:USC-SIPI-4.1.07"])
