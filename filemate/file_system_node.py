"""Abstract base class for all filesystem nodes (files and directories)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import ClassVar, Optional

from filemate.exceptions import ConfigError
from filemate.mixins import FileSystemOpsMixin, SizeComparableMixin
from filemate.node_name_cleaner import NodeNameCleaner


@dataclass
class FileSystemNode(SizeComparableMixin, FileSystemOpsMixin, ABC):
    """Base class representing a filesystem node (file or directory).

    Attributes:
        path: Absolute path to the node.
        name: Filename (basename).
        name_cleaned: Cleaned filename.
        stem: Filename without extension.
        stem_cleaned: Cleaned filename without extension.
        size: Size in bytes.
        modification_time: Last modification timestamp.
    """

    _shared_cleaner: ClassVar[Optional[NodeNameCleaner]] = None

    path: Path
    name: str = field(init=False, default="")
    name_cleaned: str = field(init=False, default="")
    stem: str = field(init=False, default="")
    stem_cleaned: str = field(init=False, default="")
    size: int = field(init=False, default=0)
    modification_time: float = field(init=False, default=0)

    @classmethod
    def set_name_cleaner(cls, cleaner: NodeNameCleaner) -> None:
        """Set the shared NodeNameCleaner for all instances.

        Args:
            cleaner: The NodeNameCleaner to share across all nodes.
        """
        cls._shared_cleaner = cleaner

    @property
    def name_cleaner(self) -> NodeNameCleaner:
        """Access the shared NodeNameCleaner.

        Returns:
            The shared NodeNameCleaner instance.

        Raises:
            ConfigError: If no cleaner has been set via ``set_name_cleaner``.
        """
        if self._shared_cleaner is None:
            raise ConfigError(
                "NodeNameCleaner not configured. "
                "Call FileSystemNode.set_name_cleaner() before creating nodes."
            )
        return self._shared_cleaner

    # -- Initialization --

    def __post_init__(self) -> None:
        """Validate path and populate derived attributes.

        Raises:
            TypeError: If *path* is not a ``pathlib.Path``.
            FileNotFoundError: If the path does not exist on disk.
        """
        if not isinstance(self.path, Path):
            raise TypeError("path must be a pathlib.Path instance")
        if not self.path.exists():
            raise FileNotFoundError(f"The node {self.path} does not exist.")
        self.path = self.path.resolve()
        self.parent = self.path.parent.resolve()
        self.name = self.path.name
        self.name_cleaned = self.name_cleaner.get_cleaned_node_name(self.path)
        self.stem = self.path.stem
        self.stem_cleaned = self.name_cleaner.get_cleaned_node_stem(self.path)
        self.modification_time = self.path.stat().st_mtime

    # -- Class check --

    def is_instance(self, node: "FileSystemNode") -> bool:
        """Check if this node is an instance of the given class.

        Args:
            node: The class to check against.

        Returns:
            True if this node is an instance of *node*.
        """
        return isinstance(self, node)

    def _instanceof(self) -> "FileSystemNode":
        """Return the concrete class of this node.

        Returns:
            The class (File or Directory).

        Raises:
            ValueError: If the node is not a FileSystemNode subclass.
        """
        if isinstance(self, FileSystemNode):
            return self.__class__
        raise ValueError("The node is not an instance of File or Directory.")

    # -- Equality and hashing (by name) --

    def __hash__(self) -> int:
        """Return hash based on name."""
        return hash(self.name)

    def __eq__(self, other: "FileSystemNode") -> bool:
        """Check equality based on name.

        Args:
            other: The other node.

        Returns:
            True if names match.
        """
        return self.name == other.name

    def __ne__(self, other: "FileSystemNode") -> bool:
        """Check inequality based on name.

        Args:
            other: The other node.

        Returns:
            True if names differ.
        """
        return self.name != other.name

    # -- String representation (abstract) --

    @abstractmethod
    def __str__(self) -> str:
        """Return a short string representation."""
        raise NotImplementedError

    @abstractmethod
    def __repr__(self) -> str:
        """Return a detailed string representation."""
        raise NotImplementedError

    # -- Reload --

    def reload(self) -> None:
        """Re-read attributes from disk.

        Raises:
            FileNotFoundError: If the path no longer exists.
        """
        try:
            self.__post_init__()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"The file {self.path} does not exist.") from e

    # -- Format / display helpers --

    def get_size(self) -> int:
        """Return the size of the node. Must be implemented by subclasses.

        Raises:
            NotImplementedError: Always (abstract).
        """
        raise NotImplementedError("The get_size method must be implemented in the subclass.")

    def human_readable_size(self, unit: str = None) -> str:
        """Convert the size into a human-readable string.

        Args:
            unit: Unused; kept for backward compatibility.

        Returns:
            Size string like ``"1.50 MB"``.
        """
        size = self.size
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} {unit}"

    def formatted_modification_time(self, datetime_format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format the modification time as a human-readable string.

        Args:
            datetime_format: ``strftime`` format string.

        Returns:
            Formatted date/time string.
        """
        return time.strftime(datetime_format, time.localtime(self.modification_time))

    # -- Type checking --

    @abstractmethod
    def get_type(self) -> None:
        """Return the semantic type of the node.

        Raises:
            NotImplementedError: Always (abstract).
        """
        raise NotImplementedError

    def is_symlink(self) -> bool:
        """Check if the node is a symbolic link.

        Returns:
            True if the path is a symlink.
        """
        return self.path.is_symlink()

    def get_year(self) -> int:
        """Extract a year (19xx/20xx) from the node name.

        Returns:
            The year as an integer, or None if no year found.
        """
        return self.name_cleaner.get_year_from_node_name(self.name)

    # -- Path operations --

    def joinpath(self, *paths) -> Path:
        """Join the node path with additional path segments.

        Args:
            *paths: Path segments to append.

        Returns:
            The joined Path.
        """
        return self.path.joinpath(*paths)

    def relative_to(self, other: Path) -> Path:
        """Return a relative path from *other* to this node.

        Args:
            other: The base path.

        Returns:
            Relative path.
        """
        return self.path.relative_to(other)

    # -- Delete (abstract) --

    def delete(self, recursive=False) -> None:
        """Delete the node.

        Args:
            recursive: If True, remove contents recursively (directories).

        Raises:
            NotImplementedError: Always (abstract).
        """
        raise NotImplementedError("The delete method must be implemented in the subclass.")
