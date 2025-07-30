class BShotException(Exception):
    """Base exception for bshot"""


class InvalidMethodException(BShotException):
    """Raised when an invalid method is passed to get_image()"""
