"""
This submodule provides functionality for low-level image input/output functions.
"""

import functools
import glob
import itertools
import operator
import os
import os.path
import pathlib
import tempfile
import time
import uuid

import cv2
import numpy as np

import dito.utils


def load(filename, color=None, np_kwargs=None, czi_kwargs=None):
    """
    Load image from file given by `filename` and return NumPy array.

    It supports all file types that can be loaded by OpenCV (via `cv2.imread`),
    plus arrays that can be loaded by NumPy (file extensions ".npy" and ".npz",
    via `numpy.load`).

    In addition, it can load ".czi" (Carl Zeiss Image) files, if the package
    `pylibCZIrw` is installed.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path of the image file to be loaded.
    color : bool or None, optional
        Whether to load the image as color (True), grayscale (False), or as is (None). Default is None.
        Is ignored if the image is loaded via NumPy (i.e., for file extensions ".npy" and ".npz").
    np_kwargs : dict
        Arguments to supply to `np.load` when loading NumPy files.
    czi_kwargs : dict
        Arguments to supply to `_load_czi` when loading ".czi" files.

    Returns
    -------
    numpy.ndarray
        The loaded image as a NumPy array.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    RuntimeError
        If the file exists, but could not be loaded.
    TypeError
        If the file exists, but its type is not a NumPy array.
    ValueError
        If the specified file is neither a NumPy file nor an image file with
        extension supported by OpenCV (".jpg", ".png", ".bmp", ".tiff", etc.).

    Notes
    -----
    The bit-depth (8 or 16 bit) of the image file will be preserved.
    """

    if isinstance(filename, pathlib.Path):
        filename = str(filename)

    # check if file exists
    if not os.path.exists(filename):
        raise FileNotFoundError("Image file '{}' does not exist".format(filename))

    # load image
    image = None
    extension = os.path.splitext(filename)[1].lower()
    if extension == ".npy":
        # use NumPy
        if color is not None:
            raise ValueError("Argument 'color' must be 'None' for NumPy images, but is '{}'".format(color))
        if np_kwargs is None:
            np_kwargs = {}
        image = np.load(file=filename, **np_kwargs)
    elif extension == ".npz":
        # use NumPy
        if np_kwargs is None:
            np_kwargs = {}
        with np.load(file=filename, **np_kwargs) as npz_file:
            npz_keys = tuple(npz_file.keys())
            if len(npz_keys) != 1:
                raise ValueError("Expected exactly one image in '{}', but got {} (keys: {})".format(filename, len(npz_keys), npz_keys))
            image = npz_file[npz_keys[0]]
    elif extension == ".czi":
        # use pylibCZIrw
        if czi_kwargs is None:
            czi_kwargs = {}
        image = _load_czi(filename=filename, **czi_kwargs)
    else:
        # use OpenCV
        if (os.name == "nt") and not dito.utils.is_ascii(s=str(filename)):
            # workaround for filenames containing non-ASCII chars under Windows
            with open(filename, "rb") as image_file:
                image = decode(b=image_file.read(), color=color)
        else:
            # all other cases
            if color is None:
                # load the image as it is
                flags = cv2.IMREAD_ANYDEPTH | cv2.IMREAD_UNCHANGED
            else:
                # force gray/color mode
                flags = cv2.IMREAD_ANYDEPTH | (cv2.IMREAD_COLOR if color else cv2.IMREAD_GRAYSCALE)
            image = cv2.imread(filename=filename, flags=flags)

    # check if loading was successful
    if image is None:
        raise RuntimeError("Image file '{}' exists, but could not be loaded".format(filename))
    if not isinstance(image, np.ndarray):
        raise TypeError("Image file '{}' exists, but has wrong type (expected object of type 'np.ndarray', but got '{}'".format(filename, type(image)))

    return image


def _load_czi(filename, keep_singleton_dimensions=False, keep_all_dimensions=False):
    """
    Load a "*.czi" (Carl Zeiss Image) image from file given by `filename` and return NumPy array.

    Internal function used by `load`. It requires the package `pylibCZIrw` to be installed.

    In addition to X, Y, and the (BGR or gray) color dimensions, CZI files can have more dimensions, such as time, Z,
    etc. The returned array will be of shape `(dim_1, dim_2, ..., dim_N, Y, X, channel_count)`, where `dim_n` is the
    size of the n-th dimension of the CZI file. The order of `dim_1`, ... `dim_N` is the same as defined in
    `pylibCZIrw.czi.CziReader.CZI_DIMS`.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path of the image file to be loaded.
    keep_singleton_dimensions : bool
        If `True`, keep dimensions in the final NumPy array even if their size is 1.
    keep_all_dimensions : bool
        If `True`, the final NumPy array will have all possible dimensions as defined in `pylibCZIrw.czi.CziReader.CZI_DIMS`.
        Dimensions not present in the CZI file will then be of size 1.

    Returns
    -------
    numpy.ndarray
        The loaded image as a NumPy array.

    Raises
    ------
    ImportError
        If `pylibCZIrw` is not installed.
    ValueError
        If `keep_all_dimensions` is `True`, but `keep_singleton_dimensions` is not.
    """

    # only import on demand
    import pylibCZIrw.czi

    # check arguments
    if keep_all_dimensions and (not keep_singleton_dimensions):
        raise ValueError("Argument 'keep_all_dimensions' is True, but 'keep_singleton_dimensions' is not")

    # be on the safe side and get all possible dimension names in the order defined by `pylibCZIrw.czi.CziReader.CZI_DIMS`
    dim_names = tuple(dim_item[0] for dim_item in sorted(pylibCZIrw.czi.CziReader.CZI_DIMS.items(), key=operator.itemgetter(1)))

    with pylibCZIrw.czi.open_czi(str(filename)) as czi:
        # get the bounding box for all dimensions
        bbox = czi.total_bounding_box

        # collect which dimensions are actually used in the image
        used_dim_names = []
        used_dim_sizes = []
        for dim_name in dim_names:
            try:
                dim_bbox = bbox[dim_name]
            except KeyError:
                # dimension is not present in this file
                if keep_all_dimensions:
                    dim_bbox = (0, 1)
                else:
                    continue

            # skip singleton dimensions if not specified otherwise
            if (not keep_singleton_dimensions) and (dim_bbox == (0, 1)):
                continue

            # if a dimension is present, assume that its bounding box is of the form (0, dim_size)
            assert dim_bbox[0] == 0
            dim_size = dim_bbox[1]

            # save used dimension name and its size
            used_dim_names.append(dim_name)
            used_dim_sizes.append(dim_size)

        # create all possible combinations for the indices of all dimensions
        used_dim_indices = [tuple(range(used_dim_size)) for used_dim_size in used_dim_sizes]
        index_product = itertools.product(*used_dim_indices)

        # for each index combination ("plane"), ...
        combined_image = None
        for indices in index_product:
            # ... get the image plane for the current index combination
            plane = {}
            for (used_dim_name, index) in zip(used_dim_names, indices):
                plane[used_dim_name] = index
            image = czi.read(plane=plane)

            # use the first plane image to get the correct shape and dtype of the final NumPy array
            if combined_image is None:
                combined_image = np.zeros(shape=tuple(used_dim_sizes) + image.shape, dtype=image.dtype)

            # insert the image plane into the final NumPy array
            combined_image[indices + (slice(None), slice(None), slice(None))] = image

    return combined_image


def load_multiple_iter(*args, color=None):
    """
    Iterator that loads all images whose filenames match a specified glob pattern.

    Parameters
    ----------
    *args : str
        Arguments that, when joined with `os.path.join`, give the file pattern of the images to load.
    color : bool or None, optional
        Whether to load the images as color (True), grayscale (False), or as is (None). Default is None. See `load`.

    Yields
    ------
    numpy.ndarray
        The loaded image as a NumPy array.
    """
    filename_pattern = os.path.join(*args)
    filenames = sorted(glob.glob(filename_pattern))
    for filename in filenames:
        image = load(filename=filename, color=color)
        yield image


def load_multiple(*args, color=None):
    """
    Load all images whose filenames match a specified glob pattern.

    Parameters
    ----------
    *args : str
        Arguments that, when joined with `os.path.join`, give the file pattern of the images to load.
    color : bool or None, optional
        Whether to load the images as color (True), grayscale (False), or as is (None). Default is None. See `load`.

    Returns
    -------
    list of numpy.ndarray
        A list of NumPy arrays, each corresponding to an image that was loaded.
    """
    return list(load_multiple_iter(*args, color=color))


def save(filename, image, mkdir=True, imwrite_params=None, np_kwargs=None, czi_kwargs=None):
    """
    Save a NumPy array `image` as an image file at `filename`.

    Supported file formats are those supported by OpenCV (via `cv2.imwrite`,
    e.g., ".jpg", ".png", ".tif", etc.) and uncompressed or compressed NumPy
    binary files (via `numpy.save` for ".npy" or via `np.savez_compressed` for
    ".npz").

    In addition, it can save ".czi" (Carl Zeiss Image) files, if the package
    `pylibCZIrw` is installed.

    If `mkdir` is `True`, create the parent directories of the given filename
    before saving the image.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to the file where the image should be saved. The extension is used
        to determine whether to use NumPy (".npy", ".npz") or OpenCV (any other
        case).
    image : numpy.ndarray
        The image data to be saved.
    mkdir : bool, optional
        Whether to create the parent directories of the given filename if they
        do not exist. Default is True.
    imwrite_params : tuple or None
        Tuple to use as value for the argument `params` of `cv2.imwrite`.
    np_kwargs : dict or None
        Arguments to supply to `np.save` (but not `np.savez_compressed` for ".npz" files) when saving NumPy files.
    czi_kwargs : dict or None
        Arguments to supply to `_save_czi` when saving ".czi" files.

    Raises
    ------
    RuntimeError
        If `image` is not a NumPy array.
    """

    if isinstance(filename, pathlib.Path):
        filename = str(filename)

    if not isinstance(image, np.ndarray):
        raise RuntimeError("Invalid image (type '{}')".format(type(image).__name__))

    # create parent dir
    if mkdir:
        dito.utils.mkdir(dirname=os.path.dirname(filename))

    extension = os.path.splitext(filename)[1].lower()
    if extension == ".npy":
        # use NumPy
        if np_kwargs is None:
            np_kwargs = {}
        np.save(file=filename, arr=image, **np_kwargs)
    elif extension == ".npz":
        # use NumPy
        np.savez_compressed(file=filename, arr_0=image)
    elif extension == ".czi":
        # use pylibCZIrw
        if czi_kwargs is None:
            czi_kwargs = {}
        _save_czi(filename=filename, image=image, **czi_kwargs)
    else:
        # use OpenCV
        if (os.name == "nt") and not dito.utils.is_ascii(s=str(filename)):
            # workaround for filenames containing non-ASCII chars under Windows
            with open(filename, "wb") as image_file:
                image_file.write(encode(image=image, extension=pathlib.Path(filename).suffix))
        else:
            # all other cases
            if imwrite_params is None:
                imwrite_params = tuple()
            cv2.imwrite(filename=filename, img=image, params=imwrite_params)


def _save_czi(
        filename, image, extra_dim_names=None, compression_options="zstd1:ExplicitLevel=10", microns_per_px_x=None,
        microns_per_px_y=None, microns_per_px_z=None, channel_names=None, document_name=None, custom_attributes=None,
):
    """
    Save a NumPy array `image` as a ".czi" (Carl Zeiss Image) file at `filename`.

    Internal function used by `save`. It requires the package `pylibCZIrw` to be installed.

    The array to be saved must be of shape `(Y, X)`, `(Y, X, 1)`, `(Y, X, 3)` or
    `(extra_dim_1, ..., extra_dim_N, Y, X, 1 | 3)`. In the latter case (i.e., more than three dimensions),
    argument `extra_dim_names` must be a string which contains one identifying letter for each extra dimension.
    Examples for identifying letters are `T` for time, `C` for channel and `Z` for Z.
    All possible identifying letters are defined in `pylibCZIrw.czi.CziReader.CZI_DIMS`.

    If, for instance, the array to be saved is of shape `(5, 25, 512, 512, 3)` with dimensions time, Z, Y, X, and color,
    then `extra_dim_names` should be `"TZ"`: `T` for time and `Z` for Z - the last three dimensions need no identifying
    letter, as they are always the same.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path of the image file to be loaded.
    image : numpy.ndarray
        The image data to be saved. Must be of shape `(Y, X)`, `(Y, X, 1)`, `(Y, X, 3)` or
        `(extra_dim_1, ..., extra_dim_N, Y, X, 1 | 3)`. In the last case (i.e., more than three dimensions),
        `extra_dim_names` must also be specified.
    extra_dim_names : None or str
        If `image` has more than three dimensions, must be specified. For each dimension not being (Y, X, color), one
        letter must be given. All possible identifying letters are defined in `pylibCZIrw.czi.CziReader.CZI_DIMS`.
    compression_options : str
        Compression options to use. Can be, among other values, `"uncompressed"` or `zstd<V>:ExplicitLevel=<N>`
        (for 0 <= V <= 1 and -131072 <= N <= 22). See `pylibCZIrw.czi.create_czi` for details.
    microns_per_px_x : None or float
        If given, will be saved in the .czi metadata as pixel scaling for the x-axis (in µm/px).
    microns_per_px_y : None or float
        If given, will be saved in the .czi metadata as pixel scaling for the y-axis (in µm/px).
    microns_per_px_z : None or float
        If given, will be saved in the .czi metadata as pixel scaling for the z-axis (in µm/px).
    channel_names : None or dict
        If given, must be a dict of the form `{0: 'Channel_0_Name', ...}`, which will then be saved in the .czi
        metadata.
    document_name : None or str
        If given, will be saved in the .czi metadata as document name.
    custom_attributes : None or dict
        If given, will be saved in the .czi metadata as arbitrary key-value store.

    Raises
    ------
    ImportError
        If `pylibCZIrw` is not installed.
    ValueError
        If `image` has an invalid shape or the image shape is not compatible with `extra_dim_names`.
    """

    # only import on demand
    import pylibCZIrw.czi

    shape = image.shape
    dim_count = len(shape)
    extra_dim_count = max(0, dim_count - 3)
    extra_dim_shape = shape[:extra_dim_count]

    if extra_dim_names is None:
        extra_dim_names = ""

    # check image dimensions
    if dim_count < 2:
        # invalid image
        raise ValueError("Invalid image shape: {}".format(shape))
    elif dim_count == 2:
        # if the image has only two axes (Y and X), add a third color axis of size of 1
        image = image[:, :, np.newaxis]
    else:
        # if the image has three or more axes, make sure that the last one is of size 1 (gray) or 3 (BGR)
        if shape[-1] not in (1, 3):
            raise ValueError("The last axis of the image must be of size 1 or 3, but it is {} (full shape: {})".format(shape[-1], shape))

        # if there are more than three axes, we need dim_names to identify which dimensions should be used
        if extra_dim_count > 0:
            # check the size of extra_dim_names
            if extra_dim_count != len(extra_dim_names):
                raise ValueError("For image of {} dimensions, 'extra_dim_names' must be of length {}-3={} (containing one identifying letter for each extra dimension), but 'extra_dim_names' is {}".format(dim_count, dim_count, extra_dim_count, extra_dim_names))

            # check if each extra dim name is correct
            allowed_dim_names = tuple(pylibCZIrw.czi.CziReader.CZI_DIMS.keys())
            for extra_dim_name in extra_dim_names:
                if extra_dim_name not in allowed_dim_names:
                    raise ValueError("Invalid dimension name '{}' - allowed values are {}".format(extra_dim_name, allowed_dim_names))

    # create all combinations of indices for extra dimensions (dimensions which are not Y, X, color)
    extra_dim_indices = [tuple(range(extra_dim_size)) for extra_dim_size in extra_dim_shape]
    extra_index_product = itertools.product(*extra_dim_indices)

    # create file
    with pylibCZIrw.czi.create_czi(
            str(filename),
            exist_ok=True,
            compression_options=compression_options,
    ) as czi:
        # for each plane (identified by the indices for the extra dimensions), write the (Y, X, color)-shaped image
        for extra_indices in extra_index_product:
            plane = {extra_dim_name: extra_index for (extra_dim_name, extra_index) in zip(extra_dim_names, extra_indices)}
            czi.write(
                data=image[extra_indices + (slice(None), slice(None), slice(None))],
                plane=plane,
            )

        # write metadata
        metadata_kwargs = {}
        if microns_per_px_x is not None:
            metadata_kwargs["scale_x"] = 1e-6 * microns_per_px_x
        if microns_per_px_y is not None:
            metadata_kwargs["scale_y"] = 1e-6 * microns_per_px_y
        if microns_per_px_z is not None:
            metadata_kwargs["scale_z"] = 1e-6 * microns_per_px_z
        if channel_names is not None:
            metadata_kwargs["channel_names"] = channel_names
        if document_name is not None:
            metadata_kwargs["document_name"] = document_name
        if custom_attributes is not None:
            metadata_kwargs["custom_attributes"] = custom_attributes
        if len(metadata_kwargs) > 0:
            czi.write_metadata(**metadata_kwargs)


def save_tmp(image):
    """
    Save a NumPy array `image` as a temporary image file and return the file path.

    The image file is saved in the temporary directory returned by `tempfile.gettempdir()`.
    The file name is constructed from the current time and a random UUID to ensure uniqueness.

    Parameters
    ----------
    image : numpy.ndarray
        The image data to be saved.

    Returns
    -------
    str
        The file path of the saved temporary image.
    """
    filename = os.path.join(tempfile.gettempdir(), "dito.save_tmp", "{}__{}.png".format(dito.utils.now_str(mode="readable"), str(uuid.uuid4()).split("-")[0]))
    save(filename=filename, image=image, mkdir=True)
    return filename


def encode(image, extension="png", params=None):
    """
    Encode the given `image` into a byte array which contains the same bytes
    as if the image would have been saved to a file.

    Parameters
    ----------
    image : numpy.ndarray
        The image to be encoded.
    extension : str, optional
        The file extension (with or without leading dot) to use for encoding the
        image. Default is "png".
    params : int or None, optional
        Parameters to pass to the encoder. These are encoder-dependent and can
        be found in the OpenCV documentation (see `cv2.imencode`). Default is
        None.

    Returns
    -------
    bytes
        A byte array which contains the encoded image data.

    See Also
    --------
    `cv2.imencode` : OpenCV function used for the encoding.
    """

    # allow extensions to be specified with or without leading dot
    if not extension.startswith("."):
        extension = "." + extension

    # use empty tuple if no params are given
    if params is None:
        params = tuple()

    (_, array) = cv2.imencode(ext=extension, img=image, params=params)

    return array.tobytes()


def decode(b, color=None):
    """
    Decode the image data from the given byte array `b` and return a NumPy array.

    The byte array should contain the *encoded* image data, which can be obtained
    with the `encode` function or by loading the raw bytes of an image file.

    Parameters
    ----------
    b : bytes
        The byte array containing the encoded image data.
    color : bool or None, optional
        Whether to load the image as color (True), grayscale (False), or as is (None). Default is None. See `load`.

    Returns
    -------
    numpy.ndarray
        The loaded image as a NumPy array.

    See Also
    --------
    `cv2.imdecode` : OpenCV function used for the decoding.
    """

    # byte array -> NumPy array
    buf = np.frombuffer(b, dtype=np.uint8)

    # flags - select grayscale or color mode
    if color is None:
        flags = cv2.IMREAD_UNCHANGED
    else:
        flags = cv2.IMREAD_ANYDEPTH | (cv2.IMREAD_COLOR if color else cv2.IMREAD_GRAYSCALE)

    # read image
    image = cv2.imdecode(buf=buf, flags=flags)

    return image


class CachedImageLoader():
    """
    A class that wraps the `load` function and caches the results.

    If `CachedImageLoader.load` is called with the same arguments again, the
    result is returned from cache and not loaded from disk.

    Notes
    -----
    The cache is only valid for the lifetime of the object. When the object is
    deleted, the cache is destroyed and all memory used by the cache is freed.

    See Also
    --------
    `functools.lru_cache` : The wrapper
    `dito.io.load` : The function that is wrapped by this class.
    """

    def __init__(self, max_count=128):
        """
        Create a new `CachedImageLoader` instance.

        Parameters
        ----------
        max_count : int, optional
            The maximum number of items that can be stored in the cache. This
            defaults to 128.
        """
        # decorate here, because maxsize can be specified by the user
        self.load = functools.lru_cache(maxsize=max_count, typed=True)(self.load)

    def load(self, filename, color=None):
        """
        Load an image from the specified file and return it as a NumPy array.

        This method is a wrapper around the `dito.load` function. The first time
        it is called with a given set of arguments, it loads the image from disk
        and returns it. Subsequent calls with the same arguments will return
        the result from cache.

        Parameters
        ----------
        filename : str or pathlib.Path
            The path to the file containing the image to load.
        color : bool or None, optional
            Whether to load the image as color (True), grayscale (False), or as is (None). Default is None. See `load`.

        Returns
        -------
        numpy.ndarray
            The loaded image as a NumPy array.

        See Also
        -----
        `dito.io.load` : The wrapped function used for image loading.
        """
        return load(filename=filename, color=color)

    def get_cache_info(self):
        """
        Get information about the cache used by this `CachedImageLoader` instance.

        Returns
        -------
        collections.namedtuple
            A named tuple with the following fields:
            - hits: number of cache hits
            - misses: number of cache misses
            - maxsize: maximum size of the cache
            - currsize: current size of the cache
        """
        return self.load.cache_info()

    def clear_cache(self):
        """
        Remove all items from the cache used by this `CachedImageLoader` instance.
        """
        self.load.cache_clear()


class VideoSaver():
    """
    Convenience wrapper for `cv2.VideoWriter`.

    Main differences compared to `cv2.VideoWriter`:
    * the parent dir of the output file is created automatically
    * the codec can be given as a string
    * the frame size is taken from the first provided image
    * the sizes of all following images are checked - if they do not match the size of the first image, an exception is
      raised
    * images are converted to gray/color mode automatically
    """

    def __init__(self, filename, codec="MJPG", fps=30.0, color=True):
        """
        Initialize the `VideoSaver` object.

        Parameters
        ----------
        filename : str or pathlib.Path
            Path to the output video file.
        codec : str, optional
            FourCC code or codec name to use for the video compression. Default is "MJPG".
        fps : float, optional
            Frames per second of the output video. Default is 30.0.
        color : bool, optional
            Whether to save the video in color (True) or grayscale (False). Default is True.

        Raises
        ------
        ValueError
            If the `codec` argument is not a string of length 4.
        """
        self.filename = filename
        self.codec = codec
        self.fps = fps
        self.color = color

        if isinstance(self.filename, pathlib.Path):
            self.filename = str(self.filename)

        if (not isinstance(self.codec, str)) or (len(self.codec) != 4):
            raise ValueError("Argument 'codec' must be a string of length 4")

        self.frame_count = 0
        self.image_size = None
        self.writer = None

    def __enter__(self):
        """
        Enter the context.

        Returns
        -------
        self
            This object.
        """
        return self

    def __exit__(self, *args, **kwargs):
        """
        Exit the context.

        Parameters
        ----------
        *args, **kwargs
            Arguments passed to the `exit` function. These are ignored.
        """
        self.save()

    def get_fourcc(self):
        """
        Return the FourCC code of the video codec.

        Returns
        -------
        int
            The FourCC code.
        """
        return cv2.VideoWriter_fourcc(*self.codec)

    def init_writer(self, image_size):
        """
        Initialize the writer object.

        Parameters
        ----------
        image_size : tuple of int
            The size of the images in the video (width, height).
        """
        self.image_size = image_size
        dito.utils.mkdir(os.path.dirname(self.filename))
        self.writer = cv2.VideoWriter(
            filename=self.filename,
            fourcc=self.get_fourcc(),
            fps=self.fps,
            frameSize=self.image_size,
            isColor=self.color,
        )

    def append(self, image):
        """
        Add a frame to the video.

        Parameters
        ----------
        image : numpy.ndarray
            The image data of the frame to add.

        Raises
        ------
        ValueError
            If the size of the image is different from the size of the previous images.
        """
        image_size = dito.core.size(image=image)

        # create writer if this is the first frame
        if self.writer is None:
            self.init_writer(image_size=image_size)

        # check if the image size is consistent with the previous frames
        if image_size != self.image_size:
            raise ValueError("Image size '{}' differs from previous image size '{}'".format(image_size, self.image_size))

        # apply correct color mode
        if self.color:
            image = dito.core.as_color(image=image)
        else:
            image = dito.core.as_gray(image=image)

        self.writer.write(image=image)
        self.frame_count += 1

    def save(self):
        """
        Finish writing the video and release the writer object.

        This method should be called after all frames have been appended to the
        video. If the `VideoSaver` object is used via a context manager, this
        method is called automatically when the context is exited.
        """
        if self.writer is not None:
            self.writer.release()

    def file_exists(self):
        """
        Check whether the output file already exists.

        Returns
        -------
        bool
            True if the output file exists, False otherwise.
        """
        return os.path.exists(path=self.filename)

    def get_file_size(self):
        """
        Get the size of the output file.

        Returns
        -------
        int
            The size of the output file in bytes.
        """
        return os.path.getsize(filename=self.filename)

    def print_summary(self, file=None):
        """
        Print a summary of the output video to the given file object or to the console.

        Parameters
        ----------
        file : file object or str, optional
            The file object to which the summary should be written, or a string
            representing the path of the file. Default is None, meaning stdout.

        Notes
        -----
        The summary includes the following information:
        * the codec
        * the filename
        * whether the output file exists
        * the size of the output file
        * the date and time the output file was last modified
        * the image size and color mode
        * the number, size, and color info of frames in the video
        """
        file_exists = self.file_exists()
        rows = [
            ["Output", ""],
            ["..Codec", self.codec],
            ["..Filename", self.filename],
            ["..Exists", file_exists],
            ["..Size", dito.utils.human_bytes(byte_count=self.get_file_size()) if file_exists else "n/a"],
            ["..Modified", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(filename=self.filename))) if file_exists else "n/a"],
            ["Frames", ""],
            ["..Size", self.image_size],
            ["..Color", self.color],
            ["..Count", self.frame_count],
        ]
        dito.utils.ptable(rows=rows, print_kwargs={"file": file})
