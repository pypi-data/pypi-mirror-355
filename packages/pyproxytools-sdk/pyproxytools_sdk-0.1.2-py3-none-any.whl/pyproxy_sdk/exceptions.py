# pyproxy_sdk/exceptions.py


class PyProxyError(Exception):
    """Base class for all PyProxy SDK exceptions."""

    pass


class PyProxyConfigurationError(PyProxyError):
    """
    Raised when client configuration is invalid
    (e.g. missing URL, username, etc.)
    """

    pass


class PyProxyAlreadyExists(PyProxyError):
    """Raised when trying to add a blocked value that already exists."""

    pass


class PyProxyNotFound(PyProxyError):
    """Raised when trying to delete a value that doesn't exist."""

    pass


class PyProxyInvalidInput(PyProxyError):
    """Raised when input data is invalid."""

    pass


class PyProxyServerError(PyProxyError):
    """Raised for unexpected server errors."""

    pass
