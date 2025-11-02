#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Helper utilities for command-line interface. """

from __future__ import annotations

import argparse
import os
import sys

# Mapping of print levels to colors
DEBUG = "debug"
INFO = "info"
WARNING = "warning"
ERROR = "error"
SUCCESS = "success"
PRINT_LEVELS_COLORS = {
    DEBUG: "cyan",
    INFO: "white",
    WARNING: "yellow",
    ERROR: "red",
    SUCCESS: "green",
}

# Colored output using termcolor (fallback to plain text if unavailable)
try:  # pylint: disable=import-outside-toplevel
    from termcolor import colored  # pylint: disable=import-error
except ImportError:  # pragma: no cover

    def colored(text, *_args, **_kwargs):  # type: ignore
        """
        Fallback colored function that returns text as-is.
        Args:
            text: The text to colorize.
            *_args: Ignored.
            **_kwargs: Ignored.
        Returns:
            The original text.
        """

        return text


def _supports_color(stream) -> bool:
    """
    Return True when color output should be used for the given stream.
    Args:
        stream: The output stream (e.g., sys.stdout, sys.stderr).
    Returns:
        True if color output is supported, False otherwise.
    """

    try:
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("FORCE_COLOR"):
            return True
        return hasattr(stream, "isatty") and stream.isatty()
    except (AttributeError, OSError):
        return False

# Determine if color output is supported for stdout and stderr
USE_COLOR_STDOUT = _supports_color(sys.stdout)
USE_COLOR_STDERR = _supports_color(sys.stderr)


def _colorize(text: str, color: str | None, enabled: bool, attrs: list[str] | None = None) -> str:
    """
    Colorize text if enabled and color is provided. Otherwise, return text as-is.
    Args:
        text: The text to colorize.
        color: The color name (e.g., 'red', 'green').
        enabled: Whether to apply colorization.
        attrs: List of attributes (e.g., ['bold', 'underline']).
    Returns:
        Colorized text or original text.
    """

    if not enabled or not color:
        return text
    return colored(text, color, attrs=attrs or [])


def print_message(text: str, level: str = INFO) -> None:
    """
    Print text with color based on level.
    Args:
        text: The text to print.
        level: The log level (DEBUG, INFO, WARNING, ERROR, SUCCESS).
    """

    color = PRINT_LEVELS_COLORS.get(level, "white")
    stream = sys.stdout if level in (DEBUG, INFO, SUCCESS) else sys.stderr
    enabled = USE_COLOR_STDOUT if stream is sys.stdout else USE_COLOR_STDERR
    print(_colorize(text, color, enabled), file=stream)
    stream.flush()


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    Returns:
        Parsed arguments.
    Raises:
        SystemExit: If parsing fails.
    """

    args_parser = argparse.ArgumentParser(
        description="FileMate - A file management tool for sorting and organizing media files"
    )
    # Positional argument
    args_parser.add_argument(
        "path",
        type=str,
        help="Path to the filesystem node to process"
    )
    # Sort flag
    args_parser.add_argument(
        "--sort",
        action="store_true",
        required=False,
        help="Sort the directory"
    )
    # Tree flag
    args_parser.add_argument(
        "--tree",
        action="store_true",
        required=False,
        help="Build the tree of the directory"
    )
    # Show tree flag
    args_parser.add_argument(
        "--show-tree",
        action="store_true",
        required=False,
        help="Show the tree of the directory"
    )
    # Clean flag
    args_parser.add_argument(
        "--clean",
        action="store_true",
        required=False,
        help="Delete remaining elements of a sorted directory"
    )
    # Verbose flag
    args_parser.add_argument(
        "--verbose",
        action="store_true",
        required=False,
        help="Verbose output"
    )
    # Dry run flag
    args_parser.add_argument(
        "--dry-run",
        action="store_true",
        required=False,
        help="Dry run"
    )
    # Version flag
    args_parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0"
    )
    return args_parser.parse_args()


def check_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    Validate command-line arguments.
    Args:
        args: Parsed arguments.
    Returns:
        Validated arguments.
    Raises:
        ValueError: If any argument is invalid.
    """

    # Required arguments validation
    from pathlib import Path

    # Validate path exists
    path = Path(args.path)
    if not path.exists():
        raise ValueError(f"Path does not exist: {args.path}")

    # Convert path string to Path object
    args.path = path

    # Optional arguments validation
    # Ensure show-tree is only used with tree
    if args.show_tree and not args.tree:
        print_message("Warning: --show-tree requires --tree flag, enabling --tree", WARNING)
        args.tree = True

    return args


def set_default_args_values(args: argparse.Namespace) -> argparse.Namespace:
    """
    Set default values for optional arguments if not provided.
    Args:
        args: Parsed arguments.
    Returns:
        Arguments with defaults set.
    Raises:
        ValueError: If any argument is invalid.
    """

    return args


__all__ = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "SUCCESS",
    "PRINT_LEVELS_COLORS",
    "print_message",
    "parse_args",
    "check_args",
    "set_default_args_values",
]
