"""
This submodule provides functionality that extends OpenCV's highgui module.
"""

import abc
import copy

import cv2

import dito.visual


class Slider(abc.ABC):
    """
    Abstract base class for creating OpenCV trackbars.

    This class and its subclasses are convenience wrappers for OpenCV's
    `cv2.createTrackbar`, `cv2.getTrackbarPos`, `cv2.setTrackbarPos`, etc.

    Attributes
    ----------
    window_name : str
        The name of the OpenCV highgui window to which the trackbar is attached.
    name : str
        The name of the trackbar.
    initial_raw_value : int
        The initial raw value of the trackbar, specified as an integer between 0 and `max_raw_value`, inclusive.
    max_raw_value : int
        The maximum raw value of the trackbar, specified as an integer greater than 0.
    changed : bool
        Indicates whether the value of the trackbar has changed since the last call to `get_raw_value()`.
    """

    def __init__(self, window_name, name, initial_raw_value, max_raw_value):
        """
        Set up and create the trackbar.

        Parameters
        ----------
        window_name : str or None
            The name of the OpenCV highgui window to attach the trackbar to. If None, the trackbar will be attached to
            `dito.visual.DEFAULT_WINDOW_NAME`.
        name : str
            The name of the trackbar.
        initial_raw_value : int
            The initial value of the trackbar, specified as an integer between 0 and `max_raw_value`, inclusive.
        max_raw_value : int
            The maximum value of the trackbar, specified as an integer greater than 0.
        """
        assert max_raw_value > 0
        assert 0 <= initial_raw_value <= max_raw_value

        self.window_name = window_name
        if self.window_name is None:
            self.window_name = dito.visual.DEFAULT_WINDOW_NAME
        self.name = name
        self.initial_raw_value = initial_raw_value
        self.max_raw_value = max_raw_value

        self.create_trackbar()
        self.changed = True

    def callback(self, raw_value):
        """
        The callback function that is called whenever the slider value is changed.

        Parameters
        ----------
        raw_value : int
            The raw value of the slider. Is not used in this method, but needed for API compliance.
            Instead, the raw value will be retrieved via `cv2.getTrackbarPos`.
        """
        self.changed = True
        self.custom_callback()

    def custom_callback(self):
        """
        Custom callback function that can be overriden by the subclass.
        """
        pass

    def create_trackbar(self):
        """
        Creates the trackbar in the OpenCV highgui window.
        """
        cv2.namedWindow(winname=self.window_name)
        cv2.createTrackbar(self.name, self.window_name, self.initial_raw_value, self.max_raw_value, self.callback)

    def get_raw_value(self):
        """
        Returns the current raw value of the slider.

        Returns
        -------
        int
            The current raw value of the slider.
        """
        self.changed = False
        return cv2.getTrackbarPos(trackbarname=self.name, winname=self.window_name)

    def set_raw_value(self, raw_value):
        """
        Sets the raw value of the slider.

        Parameters
        ----------
        raw_value : int
            The new raw value of the slider.
        """
        if raw_value < 0:
            raw_value = 0
        elif raw_value > self.max_raw_value:
            raw_value = self.max_raw_value
        cv2.setTrackbarPos(trackbarname=self.name, winname=self.window_name, pos=raw_value)

    def reset(self):
        """
        Resets the slider to its initial value.
        """
        self.set_raw_value(raw_value=self.initial_raw_value)

    @abc.abstractmethod
    def raw_from_value(self, value):
        """
        Abstract method that converts a high-level value (float, choice, etc.) to the raw integer trackbar value.

        This method needs to be overridden in derived classes.

        Parameters
        ----------
        value : object
            The high-level slider value to be converted to a raw value.

        Returns
        -------
        int
            The raw value corresponding to the slider value.
        """
        pass

    @abc.abstractmethod
    def value_from_raw(self, raw_value):
        """
        Abstract method that converts a raw integer trackbar value to a high-level value (float, choice, etc.).

        This method needs to be overridden in derived classes.

        Parameters
        ----------
        raw_value : int
            The raw trackbar value.

        Returns
        -------
        value : any
            The high-level slider value corresponding to the raw trackbar value.
        """
        pass

    def get_value(self):
        """
        Returns the current high-level value of the slider.

        Returns
        -------
        int
            The current high-level value of the slider.
        """
        raw_value = self.get_raw_value()
        return self.value_from_raw(raw_value=raw_value)

    def set_value(self, value):
        """
        Sets the high-level value of the slider.

        Parameters
        ----------
        value : int
            The new high-level value of the slider.
        """
        raw_value = self.raw_from_value(value=value)
        self.set_raw_value(raw_value=raw_value)


class ChoiceSlider(Slider):
    """
    A subclass of `Slider` that allows choosing between multiple choices.

    This slider provides a list of choices that can be selected by the user. The selected choice is returned as the
    high-level value of the slider.

    Attributes
    ----------
    choices : list
        A list of choices to select from. Each choice can be of any type.
    """

    def __init__(self, window_name, name, choices, initial_choice=None):
        """
        Set up and create the choice slider.

        Parameters
        ----------
        window_name : str or None
            The name of the OpenCV highgui window to attach the trackbar to. See `Slider.__init__`.
        name : str
            The name of the trackbar. See `Slider.__init__`
        choices : list
            The list of choices available for selection.
        initial_choice : object, optional, default: None
            The initial value of the choice slider. If None, the first element of `choices` will be used.
        """
        self.choices = copy.deepcopy(choices)
        super().__init__(
            name=name,
            window_name=window_name,
            initial_raw_value=0 if initial_choice is None else self.raw_from_value(value=initial_choice),
            max_raw_value=len(self.choices) - 1,
        )

    def raw_from_value(self, value):
        """
        Converts the high-level value (the choice) to the raw integer trackbar value.

        Parameters
        ----------
        value : object
            The high-level slider value (the choice) to be converted to a raw integer value.

        Returns
        -------
        int
            The raw integer value corresponding to the slider value.
        """
        return self.choices.index(value)

    def value_from_raw(self, raw_value):
        """
        Converts the raw integer trackbar value to a high-level value (the choice).

        Parameters
        ----------
        raw_value : int
            The raw integer trackbar value.

        Returns
        -------
        value : any
            The high-level slider value (the choice) corresponding to the raw integer trackbar value.
        """
        return self.choices[raw_value]


class BoolSlider(Slider):
    """
    A subclass of `Slider` that allows selecting a boolean value.

    This slider provides a binary choice between `False` and `True`, represented by the two ends of the slider.

    Attributes
    ----------
    None.
    """

    def __init__(self, window_name, name, initial_value=False):
        """
        Set up and create the boolean slider.

        Parameters
        ----------
        window_name : str or None
            The name of the OpenCV highgui window to attach the trackbar to. See `Slider.__init__`.
        name : str
            The name of the trackbar. See `Slider.__init__`.
        initial_value : bool, optional, default: False
            The initial value of the slider. Should be `True` or `False`.
        """
        super().__init__(
            name=name,
            window_name=window_name,
            initial_raw_value=self.raw_from_value(value=initial_value),
            max_raw_value=1,
        )

    def raw_from_value(self, value):
        """
        Converts the high-level value (the boolean value) to the raw integer trackbar value.

        Parameters
        ----------
        value : bool
            The high-level slider value (the boolean value) to be converted to a raw integer value.

        Returns
        -------
        int
            The raw integer value corresponding to the slider value.
        """
        return 1 if value else 0

    def value_from_raw(self, raw_value):
        """
        Converts the raw integer trackbar value to a high-level value (the boolean value).

        Parameters
        ----------
        raw_value : int
            The raw integer trackbar value.

        Returns
        -------
        bool
            The high-level slider value (the boolean value) corresponding to the raw integer trackbar value.
        """
        return raw_value > 0


class IntegerSlider(Slider):
    """
    A subclass of `Slider` that allows selecting an integer value within a range.

    This slider provides an integer range that can be selected by the user. The selected value is returned as the high-level value of the slider.

    Attributes
    ----------
    min_value : int
        The minimum value of the slider.
    max_value : int
        The maximum value of the slider.
    """

    def __init__(self, window_name, name, min_value, max_value, initial_value=None):
        """
        Set up and create the integer slider.

        Parameters
        ----------
        window_name : str or None
            The name of the OpenCV highgui window to attach the trackbar to. See `Slider.__init__`.
        name : str
            The name of the trackbar. See `Slider.__init__`.
        min_value : int
            The minimum value of the slider.
        max_value : int
            The maximum value of the slider.
        initial_value : int or str or None, optional, default: None
            The initial value of the slider. Can be an integer within the range `[min_value, max_value]`, or one of the following strings:
            - `"min"`: set the initial value to the minimum value of the slider.
            - `"max"`: set the initial value to the maximum value of the slider.
            - `"mean"`: set the initial value to the mean of the slider range.
            If `initial_value` is not specified, the initial value will be set to the minimum value of the slider.
        """

        self.min_value = min_value
        self.max_value = max_value

        super().__init__(
            name=name,
            window_name=window_name,
            initial_raw_value=self.raw_from_value(value=self.resolve_initial_value(initial_value=initial_value)),
            max_raw_value=self.max_value - self.min_value,
        )

    def resolve_initial_value(self, initial_value):
        """
        Resolve the initial value of the slider.

        As the initial value can also be a string, this method resolves the
        initial value of the slider from the `initial_value` parameter.

        Parameters
        ----------
        initial_value : int, str, or None
            The initial value of the slider, specified as an integer or string ("min", "max", "mean"), or None (in which case the min value is used).

        Returns
        -------
        int
            The resolved initial high-level value of the slider.

        Raises
        ------
        RuntimeError
            If `initial_value` is not an int, str, or None.
            If `initial_value` is a str, but not one of "min", "max", or "mean".
        """
        if isinstance(initial_value, int):
            return initial_value
        if initial_value is None:
            return self.min_value
        if initial_value == "min":
            return self.min_value
        if initial_value == "max":
            return self.max_value
        if initial_value == "mean":
            return (self.max_value - self.min_value) // 2 + self.min_value
        raise RuntimeError("Invalid initial value '{}'".format(initial_value))

    def raw_from_value(self, value):
        """
        Converts the high-level value to the raw integer trackbar value.

        Parameters
        ----------
        value : int
            The high-level slider value to be converted to a raw integer value.

        Returns
        -------
        int
            The raw integer value corresponding to the slider value.
        """
        return value - self.min_value

    def value_from_raw(self, raw_value):
        """
        Converts a raw integer trackbar value to the high-level value.

        Parameters
        ----------
        raw_value : int
            The raw integer trackbar value.

        Returns
        -------
        int
            The high-level slider value corresponding to the raw integer trackbar value.
        """
        return self.min_value + raw_value


class FloatSlider(Slider):
    """
    A subclass of `Slider` that allows selecting a float value within a range.

    This slider provides a float range that can be selected by the user. The selected value is returned as the high-level value of the slider.

    Attributes
    ----------
    min_value : float
        The minimum value of the slider.
    max_value : float
        The maximum value of the slider.
    """

    def __init__(self, window_name, name, min_value, max_value, value_count=101, initial_value=None):
        """
        Set up and create the float slider.

        Parameters
        ----------
        window_name : str or None
            The name of the OpenCV highgui window to attach the trackbar to. See `Slider.__init__`.
        name : str
            The name of the trackbar. See `Slider.__init__`.
        min_value : float
            The minimum value of the slider.
        max_value : float
            The maximum value of the slider.
        value_count : int, optional, default: 101
            The number of values the slider can take. This determines the precision of the slider. The slider will have
            `value_count` - 1 steps.
        initial_value : float or str or None, optional, default: None
            The initial value of the slider. Can be a float within the range `[min_value, max_value]`, or one of the following strings:
            - `"min"`: set the initial value to the minimum value of the slider.
            - `"max"`: set the initial value to the maximum value of the slider.
            - `"mean"`: set the initial value to the mean of the slider range.
            If `initial_value` is not specified, the initial value will be set to the minimum value of the slider.

        Notes
        -----
        The precision of the slider is determined by `value_count`. For example, if `value_count` is 101 and the
        slider spans the range from 0.0 to 1.0, the slider will have 100 steps of size 0.01 each.
        """
        self.min_value = min_value
        self.max_value = max_value
        self.value_count = value_count

        super().__init__(
            name=name,
            window_name=window_name,
            initial_raw_value=self.raw_from_value(value=self.resolve_initial_value(initial_value=initial_value)),
            max_raw_value=self.value_count - 1,
        )

    def resolve_initial_value(self, initial_value):
        """
        Resolve the initial value of the slider.

        Parameters
        ----------
        initial_value : float, str or None
            The initial value of the slider. See `__init__`.

        Returns
        -------
        float
            The resolved initial value.

        Raises
        ------
        RuntimeError
            If `initial_value` is not a float, None, "min", "max", or "mean".
        """
        if isinstance(initial_value, float):
            return initial_value
        if initial_value is None:
            return self.min_value
        if initial_value == "min":
            return self.min_value
        if initial_value == "max":
            return self.max_value
        if initial_value == "mean":
            return (self.max_value - self.min_value) * 0.5 + self.min_value
        raise RuntimeError("Invalid initial value '{}'".format(initial_value))

    def raw_from_value(self, value):
        """
        Converts the high-level value (the float value) to the raw integer trackbar value.

        Parameters
        ----------
        value : float
            The high-level slider value (the float value) to be converted to a raw integer value.

        Returns
        -------
        int
            The raw integer value corresponding to the slider value.
        """
        # int is required for the case that `value` is a NumPy float
        return int(round((value - self.min_value) / (self.max_value - self.min_value) * (self.value_count - 1)))

    def value_from_raw(self, raw_value):
        """
        Converts the raw integer trackbar value to a high-level value (the float value).

        Parameters
        ----------
        raw_value : int
            The raw integer trackbar value.

        Returns
        -------
        float
            The high-level slider value (the float value) corresponding to the raw integer trackbar value.
        """
        return raw_value / (self.value_count - 1) * (self.max_value - self.min_value) + self.min_value
