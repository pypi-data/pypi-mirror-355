"""
This submodule provides functionality for higher-level image analysis tasks.
"""

import abc
import collections

import cv2
import numpy as np

import dito

try:
    import sklearn.decomposition
    SKLEARN_IMPORT_ERROR = None
except ImportError as e:
    SKLEARN_IMPORT_ERROR = e


class DecompositionTextureModel(abc.ABC):
    """
    Abstract base class for texture models that decompose images into a set of texture components.

    This class provides an interface to fit a decomposition model to a set of input images
    and project them into a parameter space.

    Subclasses need to implement the `fit_decomposition` method to specify the actual decomposition
    algorithm.

    Attributes
    ----------
    image_count : int
        The number of input images in the model.
    image_shape : tuple
        The shape of the input images.
    image_dtype : np.dtype
        The data type of the input images.
    component_count : int
        The number of texture components to extract from the input images.
    keep_images : bool
        Whether to keep the input images in memory, which is useful for visualization.
    X : numpy.ndarray, shape (image_count, prod(image_shape))
        A 2D array containing the vector representations of the input images.
    P : numpy.ndarray, shape (image_count, component_count)
        A 2D array containing the projected input images into the parameter space.
    image_window_name : str
        The name of the window of the interactive visualization for displaying the images.
    slider_window_name : str
        The name of the window of the interactive visualization for displaying the sliders.

    See Also
    --------
    PcaTextureModel : A PCA-based implementation of the DecompositionTextureModel.
    NmfTextureModel : An NMF-based implementation of the DecompositionTextureModel.
    """

    def __init__(self, images, component_count, keep_images=True):
        """
        Parameters
        ----------
        images : sequence of np.ndarray
            The input images to model.
        component_count : int
            The number of texture components to extract from the input images.
        keep_images : bool, optional
            Whether to keep the input images in memory, which is useful for visualization.
            Default is `True`.
        """

        if SKLEARN_IMPORT_ERROR is not None:
            raise SKLEARN_IMPORT_ERROR

        # save images
        self.image_count = len(images)
        if self.image_count == 0:
            raise ValueError("No images were given")
        self.image_shape = images[0].shape
        self.image_dtype = images[0].dtype

        self.component_count = component_count
        self.keep_images = keep_images

        # estimate decomposition
        self.X = np.array(images).reshape(self.image_count, -1)
        self.fit_decomposition()

        # project input images into the parameter space
        if self.keep_images:
            self.P = self.decomposition.transform(self.X)
        else:
            self.X = np.zeros(shape=(0, self.X.shape[1]), dtype=self.X.dtype)
            self.P = np.zeros_like(self.X, dtype=np.float32)

        # needed for the interactive visualization
        self.image_window_name = "TextureModel - Images"
        self.slider_window_name = "TextureModel - Sliders"

    @abc.abstractmethod
    def fit_decomposition(self, *args, **kwargs):
        """
        Fit the decomposition model to the input images.

        This method needs to be overridden in derived classes.
        """
        pass

    #
    # conversion between images, image vectors (x) and parameter vectors (p)
    #

    @staticmethod
    def image_to_x(image):
        """
        Convert an image to a vector representation.

        Parameters
        ----------
        image : np.ndarray
            The input image.

        Returns
        -------
        np.ndarray
            The vector representation of the input image.
        """
        return image.reshape(1, -1)[0, :]

    def x_to_image(self, x):
        """
        Convert a vector representation to an image.

        Parameters
        ----------
        x : np.ndarray
            The input vector.

        Returns
        -------
        np.ndarray
            The image representation of the input vector.
        """
        image = x.reshape(*self.image_shape)
        dtype_range = dito.core.dtype_range(dtype=self.image_dtype)
        image = dito.core.clip(image, *dtype_range)
        image = image.astype(self.image_dtype)
        return image

    def x_to_p(self, x):
        """
        Project an image vector representation to a texture parameter vector.

        Parameters
        ----------
        x : np.ndarray
            The input image vector.

        Returns
        -------
        np.ndarray
            The corresponding texture parameter vector.
        """
        return self.decomposition.transform(x.reshape(1, -1))[0, :]

    def p_to_x(self, p):
        """
        Convert a texture parameter vector to an image vector representation.

        Parameters
        ----------
        p : np.ndarray
            The input texture parameter vector.

        Returns
        -------
        np.ndarray
            The corresponding image vector representation.
        """
        return self.decomposition.inverse_transform(p.reshape(1, -1))[0, :]

    def image_to_p(self, image):
        """
        Project an image to a texture parameter vector.

        Parameters
        ----------
        image : np.ndarray
            The input image.

        Returns
        -------
        np.ndarray
            The corresponding texture parameter vector.
        """
        x = self.image_to_x(image)
        p = self.x_to_p(x)
        return p

    def p_to_image(self, p):
        """
        Convert a texture parameter vector to an image.

        Parameters
        ----------
        p : np.ndarray
            The input texture parameter vector.

        Returns
        -------
        np.ndarray
            The corresponding image.
        """
        x = self.p_to_x(p)
        image = self.x_to_image(x)
        return image

    def get_random_p(self):
        """
        Generate a random texture parameter vector.

        Returns
        -------
        np.ndarray
            The random texture parameter vector.
        """
        return np.random.normal(loc=0.0, scale=1.0, size=(self.component_count,))

    #
    # visualization
    #

    def create_sliders(self, slider_range):
        """
        Create sliders for interactive visualization.

        The first slider is used to select an input sample, while all
        other sliders are used to control the parameter values of the
        texture model.

        Parameters
        ----------
        slider_range : tuple of float
            The range of the sliders.

        Returns
        -------
        collections.OrderedDict
            The created sliders.
        """
        sliders = collections.OrderedDict()
        sliders["sample"] = dito.highgui.IntegerSlider(
            window_name=self.slider_window_name,
            name="sample",
            min_value=0,
            max_value=self.image_count - 1,
        )
        for n_component in range(self.component_count):
            slider_name = "C{}".format(n_component + 1)
            sliders[slider_name] = dito.highgui.FloatSlider(
                window_name=self.slider_window_name,
                name=slider_name,
                min_value=slider_range[0],
                initial_value=0.0,
                max_value=slider_range[1],
                value_count=255,
            )
        return sliders

    def get_p_from_sliders(self, sliders):
        """
        Get the parameter vector from the values of the given sliders.

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to read the values from.

        Returns
        -------
        np.ndarray
            The parameter vector.
        """
        p = np.zeros(shape=(self.component_count,), dtype=np.float32)
        for n_component in range(self.component_count):
            slider_name = "C{}".format(n_component + 1)
            p[n_component] = sliders[slider_name].get_value()
        return p

    def get_image_from_sliders(self, sliders):
        """
        Get the image for the current slider values.

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to read the values from.

        Returns
        -------
        np.ndarray
            The corresponding generated image.
        """
        p = self.get_p_from_sliders(sliders)
        image = self.p_to_image(p)
        return image

    def set_sliders_from_p(self, sliders, p):
        """
        Set the slider values from a given parameter vector.

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to set the values for.
        p : np.ndarray
            The parameter vector to use for setting the slider values.
        """
        for n_component in range(self.component_count):
            slider_name = "C{}".format(n_component + 1)
            sliders[slider_name].set_value(float(p[n_component]))

    def reset_sliders(self, sliders):
        """
        Reset all sliders to their initial value (usually zero).

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to reset.
        """
        p = np.zeros(shape=(self.component_count,), dtype=np.float32)
        self.set_sliders_from_p(sliders=sliders, p=p)

    def invert_sliders(self, sliders):
        """
        Invert all slider values (multiply with -1).

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to invert.
        """
        p = self.get_p_from_sliders(sliders)
        self.set_sliders_from_p(sliders=sliders, p=-p)

    def randomize_sliders(self, sliders):
        """
        Set all slider values to random values.

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to randomize.
        """
        p = self.get_random_p()
        self.set_sliders_from_p(sliders=sliders, p=p)

    def perturb_sliders(self, sliders):
        """
        Perturb all slider values by a small random amount.

        Parameters
        ----------
        sliders : collections.OrderedDict
            The sliders to perturb.
        """
        p = self.get_p_from_sliders(sliders)
        dp = self.get_random_p() * 0.1
        self.set_sliders_from_p(sliders=sliders, p=p + dp)

    def run_interactive(self, slider_range=(-3.0, 3.0)):
        """
        Run an interactive visualization for the texture model.

        Parameters
        ----------
        slider_range : tuple of float, optional
            The range of the sliders. Default is (-3.0, 3.0).
        """

        cv2.namedWindow(self.image_window_name)
        cv2.namedWindow(self.slider_window_name)
        sliders = self.create_sliders(slider_range=slider_range)

        while True:
            if sliders["sample"].changed:
                n_sample = sliders["sample"].get_value()
                if n_sample < self.X.shape[0]:
                    x = self.X[n_sample, :]
                    p = self.x_to_p(x)
                else:
                    p = np.zeros(shape=(self.component_count,), dtype=np.float32)
                self.set_sliders_from_p(sliders, p)

            if any(slider.changed for (slider_name, slider) in sliders.items() if slider.name != "sample"):
                image = self.get_image_from_sliders(sliders)

            key = dito.visual.show(image, wait=10, window_name=self.image_window_name)
            if key in dito.visual.qkeys():
                # quit
                break
            elif key == ord("+"):
                # go to the next image
                sliders["sample"].set_value((sliders["sample"].get_value() + 1) % self.image_count)
            elif key == ord("-"):
                # go to the previous image
                sliders["sample"].set_value((sliders["sample"].get_value() - 1) % self.image_count)
            elif key == ord("n"):
                # set all parameter sliders to zero
                self.reset_sliders(sliders)
            elif key == ord("i"):
                # invert all parameter sliders
                self.invert_sliders(sliders)
            elif key == ord("r"):
                # randomize all parameter sliders
                self.randomize_sliders(sliders)
            elif key == ord("p"):
                # randomly perturb all parameter sliders
                self.perturb_sliders(sliders)
            elif key == ord("s"):
                # save current image
                image_filename = dito.io.save_tmp(image)
                print("Saved image as '{}'".format(image_filename))


class PcaTextureModel(DecompositionTextureModel):
    """
    Texture model based on principal component analysis (PCA).

    This class implements the `fit_decomposition` method of the base class `DecompositionTextureModel`
    using a principal component analysis (PCA) algorithm.
    """

    def fit_decomposition(self):
        """
        Perform the PCA-based decomposition.
        """
        self.decomposition = sklearn.decomposition.PCA(
            n_components=self.component_count,
            whiten=True,
        )
        self.decomposition.fit(self.X)


class NmfTextureModel(DecompositionTextureModel):
    """
    Texture model based on NMF (non-negative matrix factorization).

    This class implements the `fit_decomposition` method of the base class `DecompositionTextureModel`
    using a non-negative matrix factorization (NMF) algorithm.
    """

    def fit_decomposition(self):
        """
        Perform the NMF-based decomposition.
        """
        self.decomposition = sklearn.decomposition.NMF(
            n_components=self.component_count,
        )
        self.decomposition.fit(self.X)
