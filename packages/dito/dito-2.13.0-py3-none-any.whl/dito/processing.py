"""
This submodule provides functionality for basic image processing.
"""

import itertools
import math
import operator

import cv2
import numpy as np

import dito.core
import dito.visual


#
# basic processing
#


def argmin(image):
    """
    Compute the coordinates of the minimum value in the image.

    Parameters
    ----------
    image : numpy.ndarray
        The input image.

    Returns
    -------
    tuple
        The coordinates of the minimum value in the image.

    Notes
    -----
    The order of the indices is equivalent to the order of the image axes.
    This may differ from common conventions that use (x, y) coordinates.
    """
    return np.unravel_index(np.argmin(image), image.shape)


def argmax(image):
    """
    Compute the coordinates of the maximum value in the image.

    Parameters
    ----------
    image : numpy.ndarray
        The input image.

    Returns
    -------
    tuple
        The coordinates of the maximum value in the image.

    Notes
    -----
    The order of the indices is equivalent to the order of the image axes.
    This may differ from common conventions that use (x, y) coordinates.
    """
    return np.unravel_index(np.argmax(image), image.shape)


def nms_iter(image, peak_radius):
    """
    Iterate through peaks in the image using non-maximum suppression (NMS).

    The function yields peaks by repeatedly finding the maximum value in the image, suppressing its
    neighborhood within the given peak radius, and repeating the process. The iteration stops when no
    more positive values remain in the image.

    Parameters
    ----------
    image : numpy.ndarray
        The input grayscale image.
    peak_radius : int
        The radius around each peak to suppress in subsequent iterations.

    Yields
    ------
    dict
        A dictionary containing the peak index, coordinates, and value:
        - 'n_peak' : int, the index of the current peak.
        - 'peak_xy' : tuple, the (x, y) coordinates of the peak.
        - 'peak_value' : float, the value of the peak.
    """

    # peak radius must be a non-negative int
    if not (isinstance(peak_radius, int) and (peak_radius >= 0)):
        raise ValueError(f"Argument 'peak_radius' must be a non-negative integer (but is: {peak_radius})")

    # only allow images of shape (Y, X) or (Y, X, 1)
    if not dito.is_gray(image):
        raise ValueError(f"Image must be grayscale (shapes (Y, X) or (Y, X, 1)), but has shape {image.shape}")

    # remove the last singleton dimension if necessary
    image_work = image.copy()
    if len(image_work.shape) == 3:
        image_work = image_work[:, :, 0]

    for n_peak in itertools.count():
        # extract max
        (peak_y, peak_x) = argmax(image_work)
        peak_value = image_work[peak_y, peak_x]

        # stop if there are no positive values left (otherwise, we might hit an infinite loop)
        if peak_value <= 0:
            return

        # suppress neighborhood
        image_work[
            max(0, peak_y - peak_radius):min(image_work.shape[0], peak_y + peak_radius + 1),
            max(0, peak_x - peak_radius):min(image_work.shape[1], peak_x + peak_radius + 1),
        ] = 0

        yield {
            "n_peak": n_peak,
            "peak_xy": (peak_x, peak_y),
            "peak_value": peak_value,
        }


def nms(image, peak_radius, max_peak_count=1000, rel_max_value=0.1):
    """
    Perform non-maximum suppression (NMS) to extract peaks from the image.

    The function finds peaks in the image, suppressing neighboring values around each peak and iterating
    until the specified maximum peak count or relative peak value threshold is reached.

    Parameters
    ----------
    image : numpy.ndarray
        The input grayscale image.
    peak_radius : int
        The radius around each peak to suppress in subsequent iterations.
    max_peak_count : int, optional
        The maximum number of peaks to extract (default is 1000).
    rel_max_value : float, optional
        The relative peak value threshold. The extraction process stops when the peak value falls below
        this proportion of the maximum peak value (default is 0.1).

    Returns
    -------
    list of dict
        A list of dictionaries, where each dictionary contains information about a detected peak:
        - 'n_peak' : int, the index of the peak.
        - 'peak_xy' : tuple, the (x, y) coordinates of the peak.
        - 'peak_value' : the value of the peak.
    """

    # check argument 'max_peak_count'
    if not (isinstance(max_peak_count, int) and (max_peak_count >= 1)):
        raise ValueError(f"Argument 'max_peak_count' must be an integer >= 1, but is: {max_peak_count}")

    # check argument 'rel_max_value'
    if not (isinstance(rel_max_value, float) and (0.0 <= rel_max_value <= 1.0)):
        raise ValueError(f"Argument 'rel_max_value' must be a float between 0.0 and 1.0 (both inclusive), but is: {rel_max_value}")

    peaks = []
    max_value = None
    for peak in nms_iter(image=image, peak_radius=peak_radius):
        if (peak["n_peak"] + 1) >= max_peak_count:
            # stop if max peak count was reached
            break
        if max_value is None:
            # use first peak's value as reference for all other values (when comparing)
            max_value = peak["peak_value"]
        else:
            # stop if peak value is too small
            if (peak["peak_value"] / max_value) < rel_max_value:
                break
        peaks.append(peak)

    return peaks


def clipped_diff(image1, image2, scale=None, offset=None, apply_abs=False):
    """
    Compute the clipped difference between two images.

    The `image1` and `image2` inputs must have the same dtype. The function computes the element-wise difference
    between `image1` and `image2`, and then applies an optional offset and scale factor to the difference values.
    The resulting values are clipped to the original dtype range, to prevent overflow or underflow.

    Parameters
    ----------
    image1 : numpy.ndarray
        The first input image (minuend).
    image2 : numpy.ndarray
        The second input image (subtrahend).
    scale : float, optional
        The scale factor to apply to the difference values. If specified, the difference values are multiplied by
        `scale` before any offset is applied. The default value is `None`, which means no scaling is applied.
    offset : float, optional
        The offset value to add to the difference values. If specified, the difference values are increased by
        `offset` after any scaling is applied. The default value is `None`, which means no offset is applied.
    apply_abs : bool, optional
        If `True`, the absolute value of the difference image is computed after a scaling and/or offset is applied.
        The default value is `False`.

    Returns
    -------
    numpy.ndarray
        The clipped difference image, with the same shape and dtype as the input images.
    """

    # assert equal dtypes
    if image1.dtype != image2.dtype:
        raise ValueError("Both images must have the same dtypes (but have '{}' and '{}')".format(image1.dtype, image2.dtype))
    dtype = image1.dtype
    dtype_range = dito.core.dtype_range(dtype=dtype)

    # raw diff
    diff = image1.astype(np.float32) - image2.astype(np.float32)

    # apply offset, scale, and abs if specified
    if scale is not None:
        diff *= scale
    if offset is not None:
        diff += offset
    if apply_abs:
        diff = np.abs(diff)

    # clip values outside of original range
    diff = dito.clip(image=diff, lower=dtype_range[0], upper=dtype_range[1])

    return diff.astype(dtype)


def abs_diff(image1, image2):
    """
    Compute the absolute difference between two images.

    The `image1` and `image2` inputs must have the same dtype. The function computes the element-wise absolute
    difference between `image1` and `image2`, and then clips the resulting values to the original dtype range,
    to prevent overflow or underflow (which might happen for signed integer dtypes).

    Parameters
    ----------
    image1 : numpy.ndarray
        The first input image (minuend).
    image2 : numpy.ndarray
        The second input image (subtrahend).

    Returns
    -------
    numpy.ndarray
        The absolute difference image, with the same shape and dtype as the input images.
    """
    return clipped_diff(image1=image1, image2=image2, scale=None, offset=None, apply_abs=True)


def shifted_diff(image1, image2):
    """
    Compute the shifted difference between two images.

    The `image1` and `image2` inputs must have the same dtype. The function computes the element-wise difference
    between `image1` and `image2`, and then applies a scale and offset to the difference values to shift the result
    back into the original dtype range such that there is no need for clipping

    Parameters
    ----------
    image1 : numpy.ndarray
        The first input image (minuend).
    image2 : numpy.ndarray
        The second input image (subtrahend).

    Returns
    -------
    numpy.ndarray
        The shifted difference image, with the same shape and dtype as the input images.
    """
    dtype_range = dito.core.dtype_range(dtype=image1.dtype)
    return clipped_diff(image1=image1, image2=image2, scale=0.5, offset=0.5 * (dtype_range[0] + dtype_range[1]), apply_abs=False)


def gaussian_blur(image, sigma):
    """
    Apply Gaussian blur to an image.

    The filter kernel size is adapted to `sigma` automatically by OpenCV's
    `cv2.GaussianBlur`.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be blurred.
    sigma : float
        Standard deviation for Gaussian kernel. Must be greater than 0.0.

    Returns
    -------
    numpy.ndarray
        Blurred image, with the same shape and dtype as the input image.
    """
    if sigma <= 0.0:
        return image
    return cv2.GaussianBlur(src=image, ksize=None, sigmaX=sigma)


def median_blur(image, kernel_size):
    """
    Apply a median filter to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be filtered.
    kernel_size : int
        Size of the median filter kernel. Must be a positive odd integer.

    Returns
    -------
    numpy.ndarray
        Filtered image, with the same shape and dtype as the input image.
    """
    return cv2.medianBlur(src=image, ksize=kernel_size)


def clahe(image, clip_limit=None, tile_grid_size=None):
    """
    Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be equalized.
    clip_limit : float, optional
        Threshold for contrast limiting. If `None`, no clipping is performed.
        Default is `None`.
    tile_grid_size : tuple(int, int), optional
        Number of rows and columns into which the image will be divided.
        Default is `(8, 8)` (as for OpenCV).

    Returns
    -------
    numpy.ndarray
        Equalized image, with the same shape and dtype as the input image.
    """
    clahe_op = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe_op.apply(image)


#
# thresholding
#


def otsu(image):
    """
    Perform Otsu thresholding on a grayscale image.

    This function computes the optimal threshold for the input grayscale image using the Otsu method,
    and returns the thresholded image and the computed threshold.

    Parameters
    ----------
    image : numpy.ndarray
        Input grayscale image to be thresholded.

    Returns
    -------
    tuple
        A tuple containing the threshold value and the thresholded image, both as numpy.ndarray
        with the same shape and dtype as the input image.

    Raises
    ------
    ValueError
        If the input image is not grayscale.
    """
    if dito.core.is_color(image=image):
        raise ValueError("Expected gray image but got color image for Otsu thresholding")
    (theta, image2) = cv2.threshold(src=image, thresh=-1, maxval=255, type=cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return (theta, image2)


def otsu_theta(image):
    """
    Compute the Otsu threshold for a grayscale image.

    This function computes the optimal threshold for the input grayscale image using the Otsu method,
    and returns only the threshold value.

    Parameters
    ----------
    image : numpy.ndarray
        Input grayscale image.

    Returns
    -------
    float
        The computed threshold value.
    """
    (theta, image2) = otsu(image=image)
    return theta


def otsu_image(image):
    """
    Threshold a grayscale image using the Otsu method.

    This function computes the optimal threshold for the input grayscale image using the Otsu method,
    and returns the thresholded image.

    Parameters
    ----------
    image : numpy.ndarray
        Input grayscale image to be thresholded.

    Returns
    -------
    numpy.ndarray
        The thresholded image, as a numpy.ndarray with the same shape and dtype as the input image.
    """
    (theta, image2) = otsu(image=image)
    return image2


#
# morphological operations
#


def morpho_op_kernel(shape, size):
    """
    Create a morphological operation kernel.

    Parameters
    ----------
    shape : int
        Type of the kernel. The following values are supported:
        - `cv2.MORPH_RECT`: rectangular kernel
        - `cv2.MORPH_CROSS`: cross-shaped kernel
        - `cv2.MORPH_ELLIPSE`: elliptical kernel
    size : int or tuple of int
        Size (width, height) of the kernel. If a single integer is provided, assume equal width and height.

    Returns
    -------
    numpy.ndarray
        The morphological operation kernel.
    """
    ksize = dito.utils.get_validated_tuple(x=size, type_=int, count=2)
    kernel = cv2.getStructuringElement(shape=shape, ksize=ksize, anchor=(-1, -1))
    return kernel


def morpho_op(image, operation, shape=cv2.MORPH_ELLIPSE, size=3, anchor=(-1, -1), iterations=1):
    """
    Apply a morphological operation to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to which the morphological operation is applied.
    operation : int
        Type of morphological operation. The following values are supported:
        - `cv2.MORPH_ERODE`: erosion
        - `cv2.MORPH_DILATE`: dilation
        - `cv2.MORPH_OPEN`: opening
        - `cv2.MORPH_CLOSE`: closing
        - `cv2.MORPH_GRADIENT`: gradient
        - `cv2.MORPH_TOPHAT`: top hat
        - `cv2.MORPH_BLACKHAT`: black hat
    shape : int
        Type of the kernel. The following values are supported:
        - `cv2.MORPH_RECT`: rectangular kernel
        - `cv2.MORPH_CROSS`: cross-shaped kernel
        - `cv2.MORPH_ELLIPSE`: elliptical kernel
        The default value is `cv2.MORPH_ELLIPSE`.
    size : int or tuple of int
        Size (width, height) of the kernel. If a single integer is provided, assume equal width and height.
        The default value is `3`.
    anchor : tuple of int, optional
        Anchor point of the structuring element used for the morphological operation. The anchor should lie within
        the kernel. The default value is `(-1, -1)`, which means that the anchor is at the center of the kernel.
    iterations : int, optional
        Number of times the morphological operation is applied. The default value is `1`.

    Returns
    -------
    numpy.ndarray
        Resulting image after applying the morphological operation, with the same shape and dtype as the input image.
    """
    kernel = morpho_op_kernel(shape=shape, size=size)
    return cv2.morphologyEx(src=image, op=operation, kernel=kernel, anchor=anchor, iterations=iterations)


def dilate(image, **kwargs):
    """
    Apply morphological dilation to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be dilated.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Dilated image, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_DILATE, **kwargs)


def erode(image, **kwargs):
    """
    Apply morphological erosion to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be eroded.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Eroded image, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_ERODE, **kwargs)


def morpho_open(image, **kwargs):
    """
    Apply morphological opening to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be opened.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Image after the opening operation, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_OPEN, **kwargs)


def morpho_close(image, **kwargs):
    """
    Apply morphological closing to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to be closed.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Image after the closing operation, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_CLOSE, **kwargs)


def blackhat(image, **kwargs):
    """
    Apply the morphological blackhat operation to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Image after the blackhat operation, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_BLACKHAT, **kwargs)


def tophat(image, **kwargs):
    """
    Apply the morphological tophat operation to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image.
    **kwargs
        Optional arguments to be passed to `morpho_op`.

    Returns
    -------
    numpy.ndarray
        Image after the tophat operation, with the same shape and dtype as the input image.
    """
    return morpho_op(image=image, operation=cv2.MORPH_TOPHAT, **kwargs)


#
# filters
#


def dog(image, sigma1, sigma2, return_raw=False, colormap=None):
    """
    Apply the difference of Gaussians (DoG) operation to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to which the DoG is applied.
    sigma1 : float
        Standard deviation of the first Gaussian filter.
    sigma2 : float
        Standard deviation of the second Gaussian filter.
    return_raw : bool, optional
        If True, return the raw difference image. Otherwise, the difference image is shifted and scaled to match the
        original dtype range. The default value is False.
    colormap : str, optional
        Name of the colormap to use for colorizing the result. If None, no colorization is applied. The default value
        is None.

    Returns
    -------
    numpy.ndarray
        Resulting image after applying the DoG, with the same shape and dtype as the input image.
    """
    blur1 = gaussian_blur(image=image, sigma=sigma1).astype(np.float32)
    blur2 = gaussian_blur(image=image, sigma=sigma2).astype(np.float32)
    diff = blur1 - blur2
    if return_raw:
        return diff
    else:
        diff_11 = diff / dito.core.dtype_range(dtype=image.dtype)[1]
        diff_01 = (diff_11 + 1.0) * 0.5
        result = dito.convert(image=diff_01, dtype=image.dtype)
        if colormap is not None:
            result = dito.visual.colorize(image=result, colormap=colormap)
        return result


def dog_interactive(image, colormap=None):
    """
    Display an interactive window for exploring the difference of Gaussians (DoG) of an image.

    The window displays the input image, two sliders for adjusting the standard deviations of the Gaussian filters used
    in the DoG, and a visualization of the DoG result.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to which the DoG is applied.
    colormap : str, optional
        Name of the colormap to use for colorizing the result. If None, no colorization is applied. The default value
        is None.

    Returns
    -------
    None
    """
    window_name = "dito.dog_interactive"
    sliders = [dito.highgui.FloatSlider(window_name=window_name, name="sigma{}".format(n_slider + 1), min_value=0.0, max_value=15.0, value_count=1001) for n_slider in range(2)]
    sliders[0].set_value(0.5)
    sliders[1].set_value(0.8)

    image_show = None
    while True:
        if (image_show is None) or any(slider.changed for slider in sliders):
            sigmas = [sliders[n_slider].get_value() for n_slider in range(2)]
            images_blur = [gaussian_blur(image=image, sigma=sigmas[n_slider]) for n_slider in range(2)]
            images_blur = [dito.visual.text(image=image_blur, message="sigma{} = {:.2f}".format(n_slider + 1, sigmas[n_slider])) for (n_slider, image_blur) in enumerate(images_blur)]
            image_dog = dog(image, sigma1=sigmas[0], sigma2=sigmas[1], return_raw=False, colormap=colormap)
            image_show = dito.stack([[image, image_dog], images_blur])
        key = dito.show(image=image_show, window_name=window_name, wait=10)
        if key in dito.qkeys():
            return


#
# contours
#


class Contour():
    """
    A class to represent a contour.

    Attributes
    ----------
    points : numpy.ndarray
        The points that make up the contour. A 2D numpy array of shape `(n, 2)`, where `n` is the number of points
        in the contour. Each row contains the `(x, y)` coordinates of a point.
    """

    def __init__(self, points):
        """
        Parameters
        ----------
        points : numpy.ndarray
            The points defining the contour. A 2D numpy array of shape `(n, 2)`, where `n` is the number of points
            in the contour. Each row contains the `(x, y)` coordinates of a point.
        """
        self.points = points

    def __len__(self):
        """
        Return the number of points in the contour.

        Returns
        -------
        int
            The number of points in the contour.
        """
        return len(self.points)

    def __eq__(self, other):
        """
        Check if two contours are equal.

        Parameters
        ----------
        other : Contour
            Another instance of the `Contour` class.

        Returns
        -------
        bool
            True if the two contours are equal, False otherwise.
        """
        if not isinstance(other, Contour):
            raise TypeError("Argument 'other' must be a contour")

        if len(self) != len(other):
            return False

        return np.array_equal(self.points, other.points)

    def copy(self):
        """
        Return a copy of the current instance of the `Contour` class.

        Returns
        -------
        Contour
            A copy of the current instance of the `Contour` class.
        """
        return Contour(points=self.points.copy())

    def get_center(self):
        """
        Return the center point `(x, y)` of the contour.

        Returns
        -------
        numpy.ndarray
            A 2D numpy array representing the `(x, y)` coordinates of the center point of the contour.
        """
        return np.mean(self.points, axis=0)

    def get_center_x(self):
        """
        Return the x-coordinate of the center point of the contour.

        Returns
        -------
        float
            The x-coordinate of the center point of the contour.
        """
        return np.mean(self.points[:, 0])

    def get_center_y(self):
        """
        Return the y-coordinate of the center point of the contour.

        Returns
        -------
        float
            The y-coordinate of the center point of the contour.
        """
        return np.mean(self.points[:, 1])

    def get_min_x(self):
        """
        Return the minimum x-coordinate of the contour.

        Returns
        -------
        float
            The minimum x-coordinate of the contour.
        """
        return np.min(self.points[:, 0])

    def get_max_x(self):
        """
        Return the maximum x-coordinate of the contour.

        Returns
        -------
        float
            The maximum x-coordinate of the contour.
        """
        return np.max(self.points[:, 0])

    def get_width(self):
        """
        Return the width of the contour.

        Returns
        -------
        float
            The width of the contour.
        """
        return self.get_max_x() - self.get_min_x()

    def get_min_y(self):
        """
        Return the minimum y-coordinate of the contour.

        Returns
        -------
        float
            The minimum y-coordinate of the contour.
        """
        return np.min(self.points[:, 1])

    def get_max_y(self):
        """
        Return the maximum y-coordinate of the contour.

        Returns
        -------
        float
            The maximum y-coordinate of the contour.
        """
        return np.max(self.points[:, 1])

    def get_height(self):
        """
        Return the height of the contour.

        Returns
        -------
        float
            The height of the contour.
        """
        return self.get_max_y() - self.get_min_y()

    def get_area(self, mode="draw"):
        """
        Compute the area of the contour.

        Parameters
        ----------
        mode : {"draw", "calc"}, optional
            The method to use for computing the area. If "draw", the area is computed by drawing the contour as a filled
            white shape on a black image and counting the number of white pixels. If "calc", the area is computed using the
            cv2.contourArea() function. Default is "draw".

        Returns
        -------
        float
            The area of the contour.
        """
        if mode == "draw":
            image = self.draw_standalone(color=(1,), thickness=1, filled=True, antialias=False, border=2)
            return np.sum(image)

        elif mode == "calc":
            return cv2.contourArea(contour=self.points)

        else:
            raise ValueError("Invalid value for argument 'mode': '{}'".format(mode))

    def get_perimeter(self):
        """
        Compute the perimeter of the contour.

        Returns
        -------
        float
            The perimeter of the contour.
        """
        return cv2.arcLength(curve=self.points, closed=True)

    def get_circularity(self):
        """
        Compute the circularity of the contour.

        Returns
        -------
        float
            The circularity of the contour.
        """
        r_area = np.sqrt(self.get_area() / np.pi)
        r_perimeter = self.get_perimeter() / (2.0 * np.pi)
        return r_area / r_perimeter

    def get_ellipse(self):
        """
        Fit an ellipse to the contour.

        Returns
        -------
        tuple
            A tuple `(center, size, angle)`, where `center` is a tuple `(x, y)` representing the center point
            of the ellipse, `size` is a tuple `(width, height)` representing the size of the ellipse, and `angle`
            is the angle (in degrees) between the major axis of the ellipse and the x-axis.
        """
        return cv2.fitEllipse(points=self.points)

    def get_eccentricity(self):
        """
        Calculate the eccentricity of the contour.

        Returns
        -------
        float
            The eccentricity of the contour.
        """
        ellipse = self.get_ellipse()
        (width, height) = ellipse[1]
        semi_major_axis = max(width, height) * 0.5
        semi_minor_axis = min(width, height) * 0.5
        eccentricity = math.sqrt(1.0 - (semi_minor_axis / semi_major_axis)**2)
        return eccentricity

    def get_moments(self):
        """
        Calculate the moments of the contour.

        The moment values can be used to calculate various properties of the contour, such as its centroid,
        orientation, and size.

        Returns
        -------
        dict
            A dictionary of moment values for the contour.
        """
        return cv2.moments(array=self.points, binaryImage=False)

    def get_hu_moments(self, log=True):
        """
        Calculate the seven Hu moments for the contour.

        These moments are invariant shape descriptors that can be used to capture shape properties of a contour, and
        the first six of them are invariant to translation, scale, and rotation. However, the seventh moment is not
        invariant to reflection and changes its sign under reflection.

        Parameters
        ----------
        log : bool, optional
            If True (default), the logarithm of the absolute value of the Hu moments will be returned. If False, the raw
            Hu moments will be returned.

        Returns
        -------
        numpy.ndarray
            A 1D numpy array containing the seven Hu moments for the contour. If `log=True`, the values will be the
            logarithm of the absolute value of the Hu moments.
        """
        hu_moments = cv2.HuMoments(m=self.get_moments())
        if log:
            return np.sign(hu_moments) * np.log10(np.abs(hu_moments))
        else:
            return hu_moments

    def shift(self, offset_x=None, offset_y=None):
        """
        Shift the contour by a given offset along the x and/or y axis.

        Parameters
        ----------
        offset_x : float, optional
            The amount by which to shift the contour along the x-axis. If not specified, the contour is not shifted along the x-axis.
        offset_y : float, optional
            The amount by which to shift the contour along the y-axis. If not specified, the contour is not shifted along the y-axis.

        Returns
        -------
        None
        """
        if offset_x is not None:
            self.points[:, 0] += offset_x
        if offset_y is not None:
            self.points[:, 1] += offset_y

    def draw(self, image, color, thickness=1, filled=True, antialias=False, offset=None):
        """
        Draw the contour into an existing image.

        The image is changed in-place.

        Parameters
        ----------
        image : numpy.ndarray
            The image into which the contour will be drawn.
        color : tuple
            The color of the contour. Its length must equal the channel count of the image.
        thickness : int, optional
            The thickness of the contour lines. Has no effect if `filled` is True. Default is 1.
        filled : bool, optional
            Whether the contour should be filled. If True, the interior of the contour is filled with the `color` value. Default is True.
        antialias : bool, optional
            Whether antialiasing should be applied when drawing the contour. Default is False.
        offset : tuple or list or numpy.ndarray, optional
            The `(x, y)` coordinates of the offset of the contour from the origin of the image. Default is None, which corresponds to no offset.

        Returns
        -------
        None
        """
        cv2.drawContours(image=image, contours=[np.round(self.points).astype(np.int32)], contourIdx=0, color=color, thickness=cv2.FILLED if filled else thickness, lineType=cv2.LINE_AA if antialias else cv2.LINE_8, offset=offset)

    def draw_standalone(self, color, thickness=1, filled=True, antialias=False, border=0):
        """
        Draw the contour as a standalone image.

        The image has the same size as the contour (which thus is centered in the image),
        but an additional border can be specified.

        Parameters
        ----------
        color : tuple or list or numpy.ndarray
            The color of the contour. Currently, only grayscale mode is supported.
        thickness : int, optional
            The thickness of the contour lines. Has no effect if `filled` is True. Default is 1.
        filled : bool, optional
            Whether the contour should be filled. If True, the interior of the contour is filled with the `color` value. Default is True.
        antialias : bool, optional
            Whether antialiasing should be applied when drawing the contour. Default is False.
        border : int, optional
            The size of the border around the contour. Default is 0.

        Returns
        -------
        numpy.ndarray
            A 2D numpy array representing the image of the contour.
        """
        image = np.zeros(shape=(2 * border + self.get_height(), 2 * border + self.get_width()), dtype=np.uint8)
        self.draw(image=image, color=color, thickness=thickness, filled=filled, antialias=antialias, offset=(border - self.get_min_x(), border - self.get_min_y()))
        return image


class ContourList():
    """
    A class representing a list of contours.

    It allows for easy filtering of contours by various properties and offers
    additional helper functions such as drawing.

    Attributes
    ----------
    contours : list of Contour objects
        The list of contours stored in the ContourList object.
    """

    def __init__(self, contours_):
        """
        Parameters
        ----------
        contours_ : list of Contour objects
            The list of contours to be stored.
        """
        self.contours = contours_

    def __len__(self):
        """
        Return the number of contours.

        Returns
        -------
        int
            The number of contours stored in the ContourList object.
        """
        return len(self.contours)

    def __eq__(self, other):
        """
        Check if two ContourList objects are equal.

        Parameters
        ----------
        other : object
            The object to compare to.

        Returns
        -------
        bool
            True if the two objects are equal, False otherwise.

        Raises
        ------
        TypeError
            If the argument `other` is not a ContourList object.
        """
        if not isinstance(other, ContourList):
            raise TypeError("Argument 'other' must be a contour list")

        if len(self) != len(other):
            return False

        for (contour_self, contour_other) in zip(self.contours, other.contours):
            if contour_self != contour_other:
                return False

        return True

    def __getitem__(self, key):
        """
        Return the contour object at the specified index.

        Parameters
        ----------
        key : int
            The index of the contour object to be returned.

        Returns
        -------
        object
            The contour object at the specified index.
        """
        return self.contours[key]

    def copy(self):
        """
        Return a copy of the ContourList object.

        Returns
        -------
        object
            A copy of the ContourList object.
        """
        contours_copy = [contour.copy() for contour in self.contours]
        return ContourList(contours_=contours_copy)

    def filter(self, func, min_value=None, max_value=None):
        """
        Filter the contour list based on a given function and range of values.

        Only contours whose function values fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        func : function
            The function used to extract a value from each contour. It must return a value which can be compared against
            `min_value` and/or `max_value`.
        min_value : float or None, optional
            The minimum value of the extracted value for a contour to be kept. Contours with extracted values lower than
            this will be removed. If None, no minimum filter is applied. Default is None.
        max_value : float or None, optional
            The maximum value of the extracted value for a contour to be kept. Contours with extracted values higher than
            this will be removed. If None, no maximum filter is applied. Default is None.

        Returns
        -------
        None
        """
        if (min_value is None) and (max_value is None):
            # nothing to do
            return

        # filter
        contours_filtered = []
        for contour in self.contours:
            value = func(contour)
            if (min_value is not None) and (value < min_value):
                continue
            if (max_value is not None) and (value > max_value):
                continue
            contours_filtered.append(contour)
        self.contours = contours_filtered

    def filter_center_x(self, min_value=None, max_value=None):
        """
        Filter the list of contours by the x-coordinate of their centers.

        Only contours whose center x-coordinates fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        min_value : float or None, optional
            The minimum allowed value of the x-coordinate. If a contour's center x-coordinate is less than this, it is
            discarded. If None, no lower bound is applied. Default is None.
        max_value : float or None, optional
            The maximum allowed value of the x-coordinate. If a contour's center x-coordinate is greater than this, it is
            discarded. If None, no upper bound is applied. Default is None.

        Returns
        -------
        None
        """
        self.filter(func=operator.methodcaller("get_center_x"), min_value=min_value, max_value=max_value)

    def filter_center_y(self, min_value=None, max_value=None):
        """
        Filter the list of contours by the y-coordinate of their centers.

        Only contours whose center y-coordinates fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        min_value : float or None, optional
            The minimum allowed value of the y-coordinate. If a contour's center y-coordinate is less than this, it is
            discarded. If None, no lower bound is applied. Default is None.
        max_value : float or None, optional
            The maximum allowed value of the y-coordinate. If a contour's center y-coordinate is greater than this, it is
            discarded. If None, no upper bound is applied. Default is None.

        Returns
        -------
        None
        """
        self.filter(func=operator.methodcaller("get_center_y"), min_value=min_value, max_value=max_value)

    def filter_area(self, min_value=None, max_value=None, mode="draw"):
        """
        Filter the list of contours by their area.

        Only contours whose areas fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        min_value : float or None, optional
            The minimum allowed area. If a contour's area is less than this, it is discarded. If None, no lower bound
            is applied. Default is None.
        max_value : float or None, optional
            The maximum allowed area. If a contour's area is greater than this, it is discarded. If None, no upper bound
            is applied. Default is None.
        mode : str, optional
            The mode to use for computing the area. See `get_area` for details. Default is 'draw'.

        Returns
        -------
        None
        """
        self.filter(func=operator.methodcaller("get_area", mode=mode), min_value=min_value, max_value=max_value)

    def filter_perimeter(self, min_value=None, max_value=None):
        """
        Filter the list of contours by their perimeters.

        Only contours whose perimeters fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        min_value : float or None, optional
            The minimum allowed perimeter. If a contour's perimeter is less than this, it is discarded.
            If None, no lower bound is applied. Default is None.
        max_value : float or None, optional
            The maximum allowed perimeter. If a contour's perimeter is greater than this, it is discarded.
            If None, no upper bound is applied. Default is None.

        Returns
        -------
        None
        """
        self.filter(func=operator.methodcaller("get_perimeter"), min_value=min_value, max_value=max_value)

    def filter_circularity(self, min_value=None, max_value=None):
        """
        Filter the list of contours by their circularity.

        Only contours whose circularities fall within the specified range are retained.
        The contour list is modified in place.

        Parameters
        ----------
        min_value : float or None, optional
            The minimum allowed circularity. If a contour's circularity is less than this, it is discarded.
            If None, no lower bound is applied. Default is None.
        max_value : float or None, optional
            The maximum allowed circularity. If a contour's circularity is greater than this, it is discarded.
            If None, no upper bound is applied. Default is None.

        Returns
        -------
        None
        """
        self.filter(func=operator.methodcaller("get_circularity"), min_value=min_value, max_value=max_value)

    def find_largest(self, return_index=True):
        """
        Return the contour (or the contour index) with the largest area.

        Parameters
        ----------
        return_index : bool, optional
            If `True`, return the index of the largest contour. Otherwise, return the contour object itself.
            Default is `True`.

        Returns
        -------
        int or Contour or None
            The index of the largest contour if `return_index` is `True`, or the largest contour object if
            `return_index` is `False`. If no contour is found, returns None.
        """
        max_area = None
        argmax_area = None
        for (n_contour, contour) in enumerate(self.contours):
            area = contour.get_area()
            if (max_area is None) or (area > max_area):
                max_area = area
                argmax_area = n_contour

        if argmax_area is None:
            return None
        else:
            if return_index:
                return argmax_area
            else:
                return self.contours[argmax_area]

    def draw_all(self, image, colors=None, **kwargs):
        """
        Draw all the contours into an image using a different color for each contour.

        Parameters
        ----------
        image : numpy.ndarray
            The image into which the contours will be drawn.
        colors : list of tuples, optional
            The colors to use for each contour. The length of the list must be equal to the number of contours.
            If not provided, random colors will be generated. Default is None.
        **kwargs
            Additional keyword arguments to pass to the `Contour.draw()` method.

        Returns
        -------
        None
        """
        if colors is None:
            colors = tuple(dito.random_color() for _ in range(len(self)))

        for (contour, color) in zip(self.contours, colors):
            contour.draw(image=image, color=color, **kwargs)


class ContourFinder(ContourList):
    """
    Extension of `ContourList` with support to find contours in an image.

    Between OpenCV 3.x and 4.x, the API of `cv2.findContours` changed. This
    class is basically a wrapper for `cv2.findContours` which works for both
    versions.

    As a subclass of `ContourList`, it inherits all the contour list
    manipulation methods defined by its parent class.

    Attributes
    ----------
    image : numpy.ndarray
        The input image, stored as a copy of the input argument.
    contours : list of Contour
        The contours found in the input image.
    """

    def __init__(self, image):
        """
        Initialize a `ContourFinder` instance and find contours in the given `image`.

        Parameters
        ----------
        image : numpy.ndarray
            The image from which to find contours. Will be converted to dtype `numpy.uint8`
        """
        self.image = image.copy()
        if self.image.dtype == bool:
            self.image = dito.core.convert(image=self.image, dtype=np.uint8)
        contours_ = self.find_contours(image=self.image)
        super().__init__(contours_=contours_)

    @staticmethod
    def find_contours(image):
        """
        Find the contours in the given `image`.

        Parameters
        ----------
        image : numpy.ndarray
            The image from which to find contours.

        Returns
        -------
        list of Contour
            A list of instances of the `Contour` class, one for each contour found in the input image.
        """

        # find raw contours
        result = cv2.findContours(image=image, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_NONE)

        # compatible with OpenCV 3.x and 4.x, see https://stackoverflow.com/a/53909713/1913780
        contours_raw = result[-2]

        # return tuple of instances of class `Contour`
        return [Contour(points=contour_raw[:, 0, :]) for contour_raw in contours_raw]


def contours(image):
    """
    Find and return all contours in the given image.

    It is a convenience wrapper for `ContourFinder`.

    Parameters
    ----------
    image : numpy.ndarray
        The image in which to find the contours.

    Returns
    -------
    ContourList
        An instance of the `ContourList` class containing all the found contours.
    """
    contour_finder = ContourFinder(image=image)
    return contour_finder.contours


class VoronoiPartition(ContourList):
    """
    Extension of `ContourList` where the contours are derived as facets of the Voronoi partition of a set of given points.

    As a subclass of `ContourList`, it inherits all the contour list
    manipulation methods defined by its parent class.

    Attributes
    ----------
    contours : list of Contour
        The list of Voronoi facets, each represented as a `Contour` object.
    """

    def __init__(self, image_size, points):
        """
        Initialize a `VoronoiPartition` instance from a set of input points.

        Parameters
        ----------
        image_size : tuple of int
            The size of the image (width, height) in pixels.
        points : numpy.ndarray
            The array of input points for which to compute the Voronoi partition. Each row represents a point (x, y).
        """
        contours_ = self.get_facets(image_size=image_size, points=points)
        super().__init__(contours_=contours_)

    @staticmethod
    def get_facets(image_size, points):
        """
        Calculate the Voronoi partition based on the given points.

        Parameters
        ----------
        image_size : tuple of int
            The size of the image (width, height) in pixels.
        points : numpy.ndarray
            The array of input points for which to compute the Voronoi partition. Each row represents a point (x, y).

        Returns
        -------
        list of Contour
            The list of Voronoi facets, each represented as a `Contour` object.
        """
        subdiv = cv2.Subdiv2D((0, 0, image_size[0], image_size[1]))
        for point in points:
            subdiv.insert(pt=point)
        (voronoi_facets, voronoi_centers) = subdiv.getVoronoiFacetList(idx=[])
        return [Contour(voronoi_facet) for voronoi_facet in voronoi_facets]


def voronoi(image_size, points):
    """
    Compute the Voronoi partition of a set of input points.

    It is a convenience wrapper for `VoronoiPartition`.

    Parameters
    ----------
    image_size : tuple of int
        The size of the image (width, height) in pixels.
    points : numpy.ndarray
        The array of input points. Each row represents a point (x, y).

    Returns
    -------
    list of Contour
        The list of Voronoi facets, each represented as a `Contour` object.
    """
    voronoi_partition = VoronoiPartition(image_size=image_size, points=points)
    return voronoi_partition.contours
