"""Mixins extracted from FileSystemNode to reduce class size."""

from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from filemate.file_system_node import FileSystemNode


class SizeComparableMixin:
    """Mixin providing size-based arithmetic and comparison operators.

    Expects the host class to have a ``size: int`` attribute.
    """

    size: int

    def __add__(self, other: FileSystemNode) -> int:
        """Return the sum of two node sizes.

        Args:
            other: The other node.

        Returns:
            Combined size in bytes.
        """
        return self.size + other.size

    def __sub__(self, other: FileSystemNode) -> int:
        """Return the difference of two node sizes.

        Args:
            other: The other node.

        Returns:
            Size difference in bytes.
        """
        return self.size - other.size

    def __len__(self) -> int:
        """Return the size of the node.

        Returns:
            Size in bytes.
        """
        return self.size

    def __lt__(self, other: FileSystemNode) -> bool:
        """Check whether this node is smaller than *other*.

        Args:
            other: The other node.

        Returns:
            True if this node's size is less than the other's.
        """
        return self.size < other.size

    def __le__(self, other: FileSystemNode) -> bool:
        """Check whether this node is smaller than or equal to *other*.

        Args:
            other: The other node.

        Returns:
            True if this node's size is at most the other's.
        """
        return self.size <= other.size

    def __gt__(self, other: FileSystemNode) -> bool:
        """Check whether this node is larger than *other*.

        Args:
            other: The other node.

        Returns:
            True if this node's size exceeds the other's.
        """
        return self.size > other.size

    def __ge__(self, other: FileSystemNode) -> bool:
        """Check whether this node is larger than or equal to *other*.

        Args:
            other: The other node.

        Returns:
            True if this node's size is at least the other's.
        """
        return self.size >= other.size

    def __neg__(self) -> int:
        """Return the negated size.

        Returns:
            Negative size in bytes.
        """
        return -self.size

    def __pos__(self) -> int:
        """Return the positive size (identity).

        Returns:
            Size in bytes.
        """
        return +self.size

    def __abs__(self) -> int:
        """Return the absolute size.

        Returns:
            Absolute size in bytes.
        """
        return abs(self.size)

    def __round__(self, n: int = 0) -> int:
        """Round the size.

        Args:
            n: Number of decimal places.

        Returns:
            Rounded size.
        """
        return round(self.size, n)

    def __floor__(self) -> int:
        """Return the floor of the size.

        Returns:
            Floored size.
        """
        return math.floor(self.size)

    def __ceil__(self) -> int:
        """Return the ceiling of the size.

        Returns:
            Ceiled size.
        """
        return math.ceil(self.size)

    def __bool__(self) -> bool:
        """Check if the node exists and has a positive size.

        Returns:
            True if the path exists and size > 0.
        """
        return self.path.exists() and self.size > 0


class FileSystemOpsMixin:
    """Mixin providing filesystem operations (rename, move, copy, symlink, clean).

    Expects the host class to have ``path``, ``name_cleaner``, and ``reload()``
    attributes/methods.
    """

    def rename(self, new_name: str) -> None:
        """Rename the node.

        Args:
            new_name: The new filename.
        """
        new_path = self.path.parent.joinpath(new_name)
        self.path.rename(new_path)
        self.path = new_path
        self.reload()

    def move(self, new_path: Path) -> None:
        """Move the node to a new path, creating parent directories as needed.

        Args:
            new_path: Destination path.
        """
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path = new_path.resolve()
        self.path.rename(new_path)
        self.path = new_path
        self.reload()

    def copy(self, new_path: Path) -> None:
        """Copy the node to a new path.

        Args:
            new_path: Destination path.
        """
        shutil.copy(self.path, new_path)

    def create_symlink(self, target: Path, replace: bool = False) -> None:
        """Create a symbolic link pointing to *target*.

        Args:
            target: The target of the symbolic link.
            replace: If True, remove the existing path first.
        """
        if replace:
            self.path.unlink()
        self.path.symlink_to(target)

    def clean_name(self) -> None:
        """Rename the node to its cleaned name."""
        new_name = self.name_cleaner.get_cleaned_node_name(self.path)
        self.rename(new_name)
