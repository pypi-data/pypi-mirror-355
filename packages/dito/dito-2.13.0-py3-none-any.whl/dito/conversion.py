"""
This submodule provides functionality for the conversion of NumPy arrays to other formats and vice versa.
"""
import io

import cv2
import numpy as np

import dito.core
import dito.exceptions


#
# matplotlib
#


def fig_to_image(fig, size=(800, 600), savefig_kwargs=None):
    """
    Convert a Matplotlib figure to a NumPy image array.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The Matplotlib figure to convert.
    size : tuple of int, optional
        Desired output image size in pixels as (width, height). Default is (800, 600).
    savefig_kwargs : dict, optional
        Additional keyword arguments passed to `fig.savefig`. Can override default options
        like facecolor or transparency.

    Returns
    -------
    numpy.ndarray
        Image array in HWC format (height, width, 3), with BGR channels.

    Notes
    -----
    Removes alpha channel from the saved PNG to avoid transparency artifacts,
    following known Matplotlib behavior (see issue #14339).

    Examples
    --------
    >>> (fig, ax) = plt.subplots()                  # doctest: +SKIP
    >>> ax.plot([0, 1], [0, 1])                     # doctest: +SKIP
    >>> image = fig_to_image(fig, size=(400, 300))  # doctest: +SKIP
    >>> image.shape                                 # doctest: +SKIP
    (300, 400, 3)                                   # doctest: +SKIP
    """

    # set figure size in pixels
    (width, height) = size
    dpi = width / fig.get_size_inches()[0]
    fig.set_size_inches(width / dpi, height / dpi)

    # save figure to buffer
    savefig_kwargs_merged = dict(
        facecolor="white",
        transparent=False,
    )
    if savefig_kwargs is not None:
        savefig_kwargs_merged.update(savefig_kwargs)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, **savefig_kwargs_merged)

    # read image from buffer
    buffer.seek(0)
    png_bytes = np.frombuffer(buffer.getvalue(), dtype=np.uint8)
    image = cv2.imdecode(buf=png_bytes, flags=cv2.IMREAD_UNCHANGED)

    # remove alpha channel (see https://github.com/matplotlib/matplotlib/issues/14339)
    if (len(image.shape) == 3) and (image.shape[2] == 4):
        image = image[:, :, :3]

    return image


#
# PySide6
#


def to_PySide6_QPixmap_format(image):
    """
    Determine the QImage.Format which is compatible with the given image.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    PySide6.QtGui.QImage.Format
        The QImage.Format which is compatible with the given image.

    Raises
    ------
    ImportError
        If PySide6 is not installed.
    dito.exceptions.ConversionError
        If the given image cannot be converted to a compatible QImage.Format.
    """
    import PySide6.QtGui

    dtype = image.dtype
    if dito.core.is_gray(image):
        if dtype == np.uint8:
            return PySide6.QtGui.QImage.Format_Grayscale8
        elif dtype == np.uint16:
            return PySide6.QtGui.QImage.Format_Grayscale16
        else:
            raise dito.exceptions.ConversionError("Conversion of grayscale image with dtype '{}' to QPixmap is not supported".format(dtype))

    elif dito.core.is_color(image):
        if dtype == np.uint8:
            return PySide6.QtGui.QImage.Format_BGR888
        else:
            raise dito.exceptions.ConversionError("Conversion of color image with dtype '{}' to QPixmap is not supported".format(dtype))

    else:
        raise dito.exceptions.ConversionError("Conversion image with shape {} to QPixmap is not supported".format(image.shape))


def to_PySide6_QImage(image):
    """
    Convert a numpy.ndimage to PySide6.QtGui.QImage.QImage.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    PySide6.QtGui.QImage
        The QImage representation of the input image.

    Raises
    ------
    ImportError
        If PySide6 is not installed.
    """
    import PySide6.QtGui
    return PySide6.QtGui.QImage(
        np.require(image, requirements="C"),
        image.shape[1],
        image.shape[0],
        to_PySide6_QPixmap_format(image),
    )


def to_PySide6_QPixmap(image):
    """
    Convert a numpy.ndimage to PySide6.QtGui.QImage.QPixmap.

    Parameters
    ----------
    image : np.ndarray
        The input image.

    Returns
    -------
    PySide6.QtGui.QPixmap
        The QPixmap representation of the input image.

    Raises
    ------
    ImportError
        If PySide6 is not installed.
    """
    import PySide6.QtGui
    q_image = to_PySide6_QImage(image)
    return PySide6.QtGui.QPixmap(q_image)
