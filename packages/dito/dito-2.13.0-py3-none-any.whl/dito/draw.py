"""
This submodule provides functionality for drawing geometric shapes into images.
"""

import cv2
import numpy as np

import dito.core


# often-used constants
sqrt_05 = np.sqrt(0.5)


def draw_circle(image, center, radius, color, thickness, line_type, start_angle=None, end_angle=None):
    """
    Draw a circle or an arc of a circle into the given image.

    If both `start_angle` **and** `end_angle` are None, a full circle will be drawn.
    Otherwise, an arc will be drawn, assuming that a `start_angle` of None means
    0.0 degrees and an `end_angle` of None means 360.0 degrees.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    center : tuple of int
        The center of the circle as a tuple (x, y) of pixel coordinates.
    radius : int
        The radius of the circle in pixels.
    color : tuple of int
        The color of the circle as a tuple of values for each color channel.
    thickness : int, optional
        The thickness of the circle in pixels.
    line_type : int, optional
        The type of line for the circle. Possible values are `cv2.FILLED`, `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.
    start_angle : float, optional
        The starting angle of the arc in degrees. Default is None. If `end_angle` is not None, will be interpreted as 0.0.
    end_angle : float, optional
        The ending angle of the arc in degrees. Default is None. If `start_angle` is not None, will be interpreted as 360.0.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    # TODO: fix round corners when using start_angle and end_angle and thickness != cv2.FILLED
    if (start_angle is None) and (end_angle is None):
        cv2.circle(img=image, center=dito.core.tir(center), radius=radius, color=color, thickness=thickness, lineType=line_type)
    else:
        if start_angle is None:
            start_angle = 0.0
        if end_angle is None:
            end_angle = 360.0
        cv2.ellipse(img=image, center=dito.core.tir(center), axes=(radius, radius), angle=0.0, startAngle=start_angle, endAngle=end_angle, color=color, thickness=thickness, lineType=line_type)


def draw_ring(image, center, radius1, radius2, color, thickness, line_type, start_angle=None, end_angle=None):
    """
    Draw a ring (an annulus) into the given image.

    If `thickness` is `cv2.FILLED`, a filled ring will be drawn. Otherwise, an
    unfilled ring will be drawn.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    center : tuple of int
        The center of the ring as a tuple (x, y) of pixel coordinates.
    radius1 : int
        The inner radius of the ring in pixels.
    radius2 : int
        The outer radius of the ring in pixels.
    color : tuple of int
        The color of the ring as a tuple of values for each color channel.
    thickness : int
        The thickness of the ring in pixels. If `cv2.FILLED`, a filled ring is drawn.
    line_type : int
        The type of line for the ring. Possible values are `cv2.FILLED`, `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.
    start_angle : float, optional
        The starting angle of the arc in degrees. Default is None. If `end_angle` is not None, will be interpreted as 0.0.
    end_angle : float, optional
        The ending angle of the arc in degrees. Default is None. If `start_angle` is not None, will be interpreted as 360.0.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    if thickness == cv2.FILLED:
        # draw circle outline with thickness equal to the radius difference
        circle_radius = (radius1 + radius2) // 2
        circle_thickness = abs(radius1 - radius2)
        draw_circle(image=image, center=center, radius=circle_radius, color=color, thickness=circle_thickness, line_type=line_type, start_angle=start_angle, end_angle=end_angle)
    else:
        # draw two circles
        draw_circle(image=image, center=center, radius=radius1, color=color, thickness=thickness, line_type=line_type, start_angle=start_angle, end_angle=end_angle)
        draw_circle(image=image, center=center, radius=radius2, color=color, thickness=thickness, line_type=line_type, start_angle=start_angle, end_angle=end_angle)


def draw_rectangle(image, point1, point2, color, thickness, line_type):
    """
    Draw a rectangle into the given image.

    This function uses OpenCV's `cv2.rectangle` to draw a rectangle between two corner points.
    The image is modified in-place.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.line`.
    point1 : tuple of float
        One corner of the rectangle (typically top-left).
    point2 : tuple of float
        The opposite corner of the rectangle (typically bottom-right).
    color : tuple of int
        The color of the rectangle as a tuple of values for each color channel.
    thickness : int
        Thickness of the rectangle lines in pixels. Use `cv2.FILLED` to draw a filled rectangle.
    line_type : int
        The type of line used to draw the rectangle. Options include `cv2.LINE_4`, `cv2.LINE_8`, and `cv2.LINE_AA`.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    cv2.rectangle(img=image, pt1=point1, pt2=point2, color=color, thickness=thickness, lineType=line_type)


def draw_polygon(image, points, color, thickness, line_type):
    """
    Draw a polygon into the given image.

    If `thickness` is `cv2.FILLED`, a filled polygon will be drawn using
    `cv2.fillPoly`. Otherwise (positive int), an unfilled polygon will be drawn
    using `cv2.polylines`.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    points : list of tuple of float
        The vertices of the polygon, specified as a list of `(x, y)` tuples.
    color : tuple of int
        The color of the polygon as a tuple of values for each color channel.
    thickness : int
        The thickness of the polygon lines in pixels. If `cv2.FILLED`, a filled polygon is drawn.
    line_type : int
        The type of line for the polygon. Possible values are `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    points_int = np.round(np.array(points)).astype(np.int32)
    if thickness == cv2.FILLED:
        cv2.fillPoly(img=image, pts=[points_int], color=color, lineType=line_type)
    else:
        cv2.polylines(img=image, pts=[points_int], isClosed=True, color=color, thickness=thickness, lineType=line_type)


def draw_regular_polygon(image, point_count, position, radius, color, thickness, line_type, angle_offset=0.0):
    """
    Draw a regular polygon (e.g., a triangle, square, pentagon) into the given image.

    The polygon will be centered at `position` and have `radius` as the distance from
    the center to each vertex. The number of vertices is specified by `point_count`.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    point_count : int
        The number of vertices of the polygon. E.g. `point_count=3` draws a triangle, `point_count=4` draws a square, etc.
    position : tuple of float
        The center of the polygon as a tuple `(x, y)` of pixel coordinates.
    radius : float
        The radius of the polygon in pixels, i.e. the distance from the center to each vertex.
    color : tuple of int
        The color of the polygon as a tuple of values for each color channel.
    thickness : int
        The thickness of the polygon lines in pixels. If `cv2.FILLED`, a filled polygon is drawn.
    line_type : int
        The type of line for the polygon. Possible values are `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.
    angle_offset : float, optional
        An angle offset (in radians) for the polygon vertices. This can be used to rotate the polygon. Default is 0.0 radians.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    (x, y) = position
    points = []
    for angle in np.linspace(start=0.0, stop=2.0 * np.pi, num=point_count, endpoint=False):
        points.append([
            radius * np.cos(angle + angle_offset) + x,
            radius * np.sin(angle + angle_offset) + y,
        ])
    draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)


def draw_regular_star(image, point_count, position, radius_outer, radius_inner, color, thickness, line_type, angle_offset=0.0):
    """
    Draw a regular star shape into the given image.

    In contrast to `draw_regular_polygon` where the distance from the center to
    each vertex is constant, this function draws a regular star shape, where
    the distance from the center to each vertex alternates between two different
    radii.

    The star will be centered at `position` and have `radius_outer` as the distance from
    the center to the outermost vertices, and `radius_inner` as the distance from the
    center to the innermost vertices. The number of vertices is specified by `point_count`.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    point_count : int
        The number of vertices of the star.
    position : tuple of float
        The center of the star as a tuple `(x, y)` of pixel coordinates.
    radius_outer : float
        The outer radius of the star in pixels, i.e. the distance from the center to the outermost vertices.
    radius_inner : float
        The inner radius of the star in pixels, i.e. the distance from the center to the innermost vertices.
    color : tuple of int
        The color of the star as a tuple of values for each color channel.
    thickness : int
        The thickness of the star lines in pixels. If `cv2.FILLED`, a filled star is drawn.
    line_type : int
        The type of line for the star. Possible values are `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.
    angle_offset : float, optional
        An angle offset (in radians) for the star vertices. This can be used to rotate the star. Default is 0.0 radians.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    (x, y) = position
    points = []
    for (n_point, angle) in enumerate(np.linspace(start=0.0, stop=2.0 * np.pi, num=2 * point_count, endpoint=False)):
        radius = radius_outer if (n_point % 2) == 0 else radius_inner
        points.append([
            radius * np.cos(angle + angle_offset) + x,
            radius * np.sin(angle + angle_offset) + y,
        ])
    draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)


def draw_regular_skeleton(image, point_count, position, radius, color, thickness, line_type, angle_offset=0.0):
    """
    Draw a regular polygon skeleton into the given image.

    It is similar to `draw_regular_polygon`, but draws only lines from the
    center to each vertex, instead of a filled or unfilled polygon.

    The skeleton will be centered at `position` and have `radius` as the distance from
    the center to each vertex. The number of vertices is specified by `point_count`.

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    point_count : int
        The number of vertices of the skeleton.
    position : tuple of float
        The center of the polygon as a tuple `(x, y)` of pixel coordinates.
    radius : float
        The radius of the polygon in pixels, i.e. the distance from the center to each vertex.
    color : tuple of int
        The color of the polygon as a tuple of values for each color channel.
    thickness : int
        The thickness of the polygon lines in pixels. `cv2.FILLED` is interpreted as `thickness=1`, as this is not a polygon.
    line_type : int
        The type of line for the skeleton. Possible values are `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`.
    angle_offset : float, optional
        An angle offset (in radians) for the skeleton vertices. This can be used to rotate the polygon. Default is 0.0 radians.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """
    thickness = 1 if thickness == cv2.FILLED else thickness
    (x, y) = position
    for angle in np.linspace(start=0.0, stop=2.0 * np.pi, num=point_count, endpoint=False):
        cv2.line(img=image, pt1=dito.core.tir(x, y), pt2=dito.core.tir(radius * np.cos(angle + angle_offset) + x, radius * np.sin(angle + angle_offset) + y), color=color, thickness=thickness, lineType=line_type)


def draw_symbol(image, symbol, position, radius=4, color=None, thickness=1, line_type=cv2.LINE_AA):
    """
    Draw a symbol into the given image.

    The symbol is centered at `position` and has `radius` as its size. The available symbols are:
    - 'circle' or 'o': draw a circle
    - 'cross' or 'x': draw a cross
    - 'diamond' or 'D': draw a diamond
    - 'diamond_thin' or 'd': draw a thin diamond
    - 'hexagon' or '6': draw a hexagon
    - 'pentagon' or '5': draw a pentagon
    - 'plus' or '+': draw a plus sign
    - 'skeleton_5': draw a skeleton of a pentagon
    - 'skeleton_6': draw a skeleton of a hexagon
    - 'square' or '4': draw a square
    - 'star_4': draw a four-pointed star
    - 'star_5' or '*': draw a five-pointed star
    - 'star_6': draw a six-pointed star
    - 'star_12': draw a twelve-pointed star
    - 'triangle_up' or '^': draw an upward-facing triangle
    - 'triangle_down' or 'v': draw a downward-facing triangle
    - 'triangle_left' or '<': draw a left-facing triangle
    - 'triangle_right' or '>': draw a right-facing triangle
    - 'y_up': draw an upward-facing 'Y' symbol
    - 'y_down' or 'Y': draw a downward-facing 'Y' symbol
    - 'y_left': draw a left-facing 'Y' symbol
    - 'y_right': draw a right-facing 'Y' symbol

    Parameters
    ----------
    image : numpy.ndarray
        Input image to draw into. This image will be altered in-place, just like using similar OpenCV drawing functions such as `cv2.circle`.
    symbol : str
        The symbol to draw.
    position : tuple of float
        The center of the symbol as a tuple `(x, y)` of pixel coordinates.
    radius : float, optional
        The radius of the symbol in pixels. Default is 4 pixels.
    color : tuple of int or None, optional
        The color of the symbol as a tuple of values for each color channel. If None, the color is automatically chosen based on the image type (green for color images and white for grayscale images). Default is None.
    thickness : int, optional
        The thickness of the symbol lines in pixels. If `cv2.FILLED`, a filled symbol is drawn. Default is 1 pixel.
    line_type : int, optional
        The type of line for the symbol. Possible values are `cv2.LINE_4`, `cv2.LINE_8`, `cv2.LINE_AA`. Default is `cv2.LINE_AA`.

    Note
    ----
    The image is altered in-place.

    Returns
    -------
    None
    """

    # handle arguments
    (x, y) = position
    if color is None:
        if dito.core.is_color(image=image):
            color = (0, 255, 0)
        else:
            color = (255,)

    if symbol in ("circle", "o"):
        cv2.circle(img=image, center=dito.core.tir(x, y), radius=radius, color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("cross", "x"):
        thickness = 1 if thickness == cv2.FILLED else thickness
        sqrt_one_over_radius = sqrt_05 * radius
        cv2.line(img=image, pt1=dito.core.tir(x - sqrt_one_over_radius, y - sqrt_one_over_radius), pt2=dito.core.tir(x + sqrt_one_over_radius, y + sqrt_one_over_radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=dito.core.tir(x + sqrt_one_over_radius, y - sqrt_one_over_radius), pt2=dito.core.tir(x - sqrt_one_over_radius, y + sqrt_one_over_radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("diamond", "D"):
        points = [
            (x, y - radius),
            (x + radius, y),
            (x, y + radius),
            (x - radius, y),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("diamond_thin", "d"):
        points = [
            (x, y - radius),
            (x + 0.67 * radius, y),
            (x, y + radius),
            (x - 0.67 * radius, y),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("hexagon", "6"):
        draw_regular_polygon(image=image, point_count=6, position=position, radius=radius, color=color, thickness=thickness, line_type=line_type, angle_offset=1.5 * np.pi)

    elif symbol in ("pentagon", "5"):
        draw_regular_polygon(image=image, point_count=5, position=position, radius=radius, color=color, thickness=thickness, line_type=line_type, angle_offset=1.5 * np.pi)

    elif symbol in ("plus", "+"):
        thickness = 1 if thickness == cv2.FILLED else thickness
        cv2.line(img=image, pt1=dito.core.tir(x - radius, y), pt2=dito.core.tir(x + radius, y), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=dito.core.tir(x, y - radius), pt2=dito.core.tir(x, y + radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("skeleton_5",):
        draw_regular_skeleton(image=image, point_count=5, position=position, radius=radius, color=color, thickness=thickness, line_type=line_type, angle_offset=1.5 * np.pi)

    elif symbol in ("skeleton_6",):
        draw_regular_skeleton(image=image, point_count=6, position=position, radius=radius, color=color, thickness=thickness, line_type=line_type, angle_offset=0.5 * np.pi)

    elif symbol in ("square", "4"):
        cv2.rectangle(img=image, pt1=dito.core.tir(x - radius, y - radius), pt2=dito.core.tir(x + radius, y + radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("star_4",):
        draw_regular_star(image=image, point_count=4, position=position, radius_outer=radius, radius_inner=0.5 * radius, color=color, thickness=thickness, line_type=line_type, angle_offset=1.5 * np.pi)

    elif symbol in ("star_5", "*"):
        draw_regular_star(image=image, point_count=5, position=position, radius_outer=radius, radius_inner=0.5 * radius, color=color, thickness=thickness, line_type=line_type, angle_offset=1.5 * np.pi)

    elif symbol in ("star_6",):
        draw_regular_star(image=image, point_count=6, position=position, radius_outer=radius, radius_inner=0.5 * radius, color=color, thickness=thickness, line_type=line_type, angle_offset=0.5 * np.pi)

    elif symbol in ("star_12",):
        draw_regular_star(image=image, point_count=12, position=position, radius_outer=radius, radius_inner=0.5 * radius, color=color, thickness=thickness, line_type=line_type, angle_offset=0.5 * np.pi)

    elif symbol in ("triangle_up", "^"):
        points = [
            (x, y - radius),
            (x + radius, y + sqrt_05 * radius),
            (x - radius, y + sqrt_05 * radius),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("triangle_down", "v"):
        points = [
            (x + radius, y - sqrt_05 * radius),
            (x - radius, y - sqrt_05 * radius),
            (x, y + radius),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("triangle_left", "<"):
        points = [
            (x + sqrt_05 * radius, y - radius),
            (x - radius, y),
            (x + sqrt_05 * radius, y + radius),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("triangle_right", ">"):
        points = [
            (x - sqrt_05 * radius, y - radius),
            (x + radius, y),
            (x - sqrt_05 * radius, y + radius),
        ]
        draw_polygon(image=image, points=points, color=color, thickness=thickness, line_type=line_type)

    elif symbol in ("y_up",):
        thickness = 1 if thickness == cv2.FILLED else thickness
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x, y - radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x + sqrt_05 * radius, y + sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x - sqrt_05 * radius, y + sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("y_down", "Y"):
        thickness = 1 if thickness == cv2.FILLED else thickness
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x + sqrt_05 * radius, y - sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x - sqrt_05 * radius, y - sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x, y + radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("y_left",):
        thickness = 1 if thickness == cv2.FILLED else thickness
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x - radius, y), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x + sqrt_05 * radius, y - sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x + sqrt_05 * radius, y + sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)

    elif symbol in ("y_right",):
        thickness = 1 if thickness == cv2.FILLED else thickness
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x - sqrt_05 * radius, y - sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x - sqrt_05 * radius, y + sqrt_05 * radius), color=color, thickness=thickness, lineType=line_type)
        cv2.line(img=image, pt1=(x, y), pt2=dito.core.tir(x + radius, y), color=color, thickness=thickness, lineType=line_type)

    else:
        raise ValueError("Unknown symbol '{}'".format(symbol))
