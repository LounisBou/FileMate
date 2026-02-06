"""Custom exception hierarchy for FileMate."""


class FileMateError(Exception):
    """Base exception for all FileMate errors."""


class ConfigError(FileMateError):
    """Raised for configuration-related errors."""


class NodeNotFoundError(FileMateError):
    """Raised when a filesystem node cannot be found."""


class SortingError(FileMateError):
    """Raised when a sorting operation fails."""


class TransferError(FileMateError):
    """Raised when a packer transfer operation fails."""
