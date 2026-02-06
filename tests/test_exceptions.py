"""Tests for the custom exception hierarchy."""

import pytest

from filemate.exceptions import (
    ConfigError,
    FileMateError,
    NodeNotFoundError,
    SortingError,
    TransferError,
)


def test_hierarchy():
    """All custom exceptions are subclasses of FileMateError and Exception."""
    for exc_cls in (ConfigError, NodeNotFoundError, SortingError, TransferError):
        assert issubclass(exc_cls, FileMateError)
        assert issubclass(exc_cls, Exception)


def test_messages():
    """Each exception carries a message string."""
    for exc_cls in (ConfigError, NodeNotFoundError, SortingError, TransferError):
        exc = exc_cls("test message")
        assert str(exc) == "test message"


def test_catch_base():
    """Catching FileMateError catches all subclasses."""
    for exc_cls in (ConfigError, NodeNotFoundError, SortingError, TransferError):
        with pytest.raises(FileMateError):
            raise exc_cls("caught via base")
