

class BaseLazyImportException(Exception):
    """Base class for all lazy_import exceptions"""

class LazyImportError(ImportError, BaseLazyImportException):
    """Subclass of ImportError. Raised when there are issues with lazily importing modules"""

class LazyImportRuntimeError(BaseLazyImportException):
    """Raised by un-allowed dynamic behavior within a "with lazy:" block"""

class NotLazyEnoughError(AttributeError, BaseLazyImportException):
    """Raised when a lazy-loaded module is accessed before execution leaves the "with lazy:" block"""