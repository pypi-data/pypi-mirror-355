"""
This submodule defines exception classes used within dito.
"""


class DitoException(Exception):
    """Base exception class for Dito."""


class ConversionError(DitoException):
    """Raised when a conversion to a different data type fails."""


class InvalidImageShapeError(DitoException):
    """Raised when an image has an invalid shape, e.g. too few or too many dimensions."""


class QkeyInterrupt(DitoException):
    """Raised when the user presses the Q key during an image display, causing the display to be closed."""


class ParseShapeError(DitoException):
    """Base exception for `parse_shape`-related errors."""
    pass


class ParseShapeDefinitionError(ParseShapeError):
    """Raised when the shape definition string is invalid."""


class ParseShapeMismatchError(ParseShapeError):
    """Raised when the shape does not match the shape definition."""
    pass
