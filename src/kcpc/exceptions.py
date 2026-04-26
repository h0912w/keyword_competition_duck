"""Custom exceptions for KCPC."""


class KcpcError(Exception):
    """Base exception for KCPC errors."""

    pass


class FileIOError(KcpcError):
    """Raised when file input/output operations fail."""

    pass


class DatabaseError(KcpcError):
    """Raised when database operations fail."""

    pass


class MeasurementError(KcpcError):
    """Raised when keyword measurement fails."""

    pass


class ValidationError(KcpcError):
    """Raised when input validation fails."""

    pass


class ExportError(KcpcError):
    """Raised when export operations fail."""

    pass
