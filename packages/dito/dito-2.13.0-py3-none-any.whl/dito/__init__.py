"""
`dito` is yet another toolbox for the daily work with OpenCV under Python.

* Code: https://github.com/dhaase-de/dito
* PyPI: https://pypi.org/project/dito/
* Documentation: https://dhaase-de.github.io/dito/dito.html

It provides convenience wrappers for frequently used image-related
functionalities in OpenCV and NumPy, as well as additional functionality built
on top of them.

The module follows the data conventions of OpenCV under Python, namely:
* images are represented as `numpy.ndarray`s with shape `(?, ?)` or `(?, ?, 1)`
  (grayscale) or `(?, ?, 3)` (color)
* the color channel order is BGR
* the value range for float images is `(0.0, 1.0)`
* point coordinates are given in `(x, y[, z])` order
* images sizes (not shapes--these have the same meaning as in NumPy) are given
  in `(width, height)` order
* arguments such as `line_type`, `interpolation`, etc. expect values defined by
  OpenCV (e.g., `cv2.LINE_AA`, `cv2.INTER_LINEAR`, etc.)

All submodules are imported and can be accessed directly through the `dito`
namespace. For example, `dito.io.load` can be accessed as `dito.load`.

The code is structured into the following submodules:

Submodule         | Description                                                       | Example
------------------|-------------------------------------------------------------------|--------------------------------
`dito.analysis`   | higher-level image analysis tasks                                 | `dito.analysis.PcaTextureModel`
`dito.conversion` | conversion of images represented as NumPy images to other formats | `dito.conversion.to_PySide6_QPixmap`
`dito.core`       | core image-related functionality                                  | `dito.core.normalize`
`dito.data`       | pre-defined images and other data (colormaps, fonts, etc.)        | `dito.data.pm5544`
`dito.draw`       | basic image drawing                                               | `dito.draw.draw_symbol`
`dito.exceptions` | exception classes used within `dito`                              | `dito.exceptions.ConversionError`
`dito.highgui`    | extensions for OpenCV's built-in `highgui` module                 | `dito.highgui.FloatSlider`
`dito.inspection` | functions for inspecting images and their properties              | `dito.inspection.pinfo`
`dito.io`         | low-level image input/output functions                            | `dito.io.load`
`dito.parallel`   | functions for parallelizing image processing                      | `dito.parallel.mp_starmap`
`dito.processing` | basic image processing                                            | `dito.processing.contours`
`dito.utils`      | utility functions used throughout `dito`                          | `dito.utils.now_str`
`dito.visual`     | functions for visualizing images                                  | `dito.visual.text`
"""

__version__ = "2.13.0"


from dito.analysis import *
from dito.conversion import *
from dito.core import *
from dito.data import *
from dito.draw import *
from dito.exceptions import *
from dito.highgui import *
from dito.inspection import *
from dito.io import *
from dito.parallel import *
from dito.processing import *
from dito.utils import *
from dito.visual import *
