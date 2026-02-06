"""Directory node implementation."""

import os
import shutil
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Union

from filemate.file import File
from filemate.file_system_node import FileSystemNode
from filemate.file_type import FileType
from filemate.file_type_extensions import FileTypeExtensions


@dataclass(eq=False)
class Directory(FileSystemNode):
    """A filesystem node representing a directory.

    Attributes:
        year: Year extracted from the directory name, or 0.
        recursive: If True, iteration includes subdirectory contents.
    """

    year: int | None = field(init=False, default=0)
    recursive: bool = field(init=False, default=False)

    # -- Initialization --

    def __post_init__(self) -> None:
        """Initialize directory-specific attributes.

        Raises:
            ValueError: If the path is not a directory.
        """
        super().__post_init__()
        if not self.path.is_dir():
            raise ValueError(f"The path {self.path} is not a directory.")
        self.stem = self.name.split(" (", maxsplit=1)[0]
        self.year = self.name_cleaner.get_year_from_node_name(self.name)

    # -- String representation --

    def __str__(self) -> str:
        """Return ``'Directory: <name>'``."""
        return f"Directory: {self.path.name}"

    def __repr__(self) -> str:
        """Return a multi-line detail string."""
        return (
            f"Directory: {self.path}\n"
            f"Name: {self.name}\n"
            f"Name Cleaned: {self.name_cleaned}\n"
            f"Stem: {self.stem}\n"
            f"Stem Cleaned: {self.stem_cleaned}\n"
            f"Year: {self.year}\n"
            f"Size: {self.human_readable_size()}\n"
            f"Items: {self.count()}\n"
            f"  - Files: {self.count_files()}\n"
            f"  - Subdirectories: {self.count_dirs()}\n"
            f"Recursive: {self.recursive}\n"
            f"Last Modified: {self.formatted_modification_time()}\n"
            f"Type: {self.get_type()}"
        )

    # -- Iteration and containment --

    def __iter__(self) -> Iterator[FileSystemNode]:
        """Iterate over directory contents.

        Returns:
            Iterator of FileSystemNode instances.
        """
        return self.iter(recursive=self.recursive)

    def __next__(self) -> FileSystemNode:
        """Return the next node in the directory."""
        return next(self.iter(recursive=self.recursive))

    def __contains__(self, node: FileSystemNode) -> bool:
        """Check whether *node* is in this directory.

        Args:
            node: The node to look for.

        Returns:
            True if found.
        """
        target_name = node.path.name
        with os.scandir(self.path) as entries:
            for entry in entries:
                if entry.name == target_name:
                    return True
        if getattr(self, "recursive", False):
            for _, dirs, files in os.walk(self.path):
                if target_name in files or target_name in dirs:
                    return True
        return False

    def __getitem__(self, search: str) -> FileSystemNode:
        """Get a child node by name.

        Args:
            search: Filename or hash to look up.

        Returns:
            The matching FileSystemNode.

        Raises:
            KeyError: If no match is found.
        """
        for node in self.iter(recursive=self.recursive):
            if node.name == search or hash(node) == search:
                return node
        raise KeyError(f"No node {search} in the directory {self.path}")

    def __setitem__(self, search: str, new_node: FileSystemNode) -> None:
        """Replace a child node by name.

        Args:
            search: Filename or hash to look up.
            new_node: The replacement node.

        Raises:
            KeyError: If no match is found.
        """
        for node in self.iter(recursive=self.recursive):
            if node.name == search or hash(node) == search:
                node.move(new_node.path)
                return
        raise KeyError(f"No node {search} in the directory {self.path}")

    def __delitem__(self, search: str) -> None:
        """Delete a child node by name.

        Args:
            search: Filename or hash to look up.

        Raises:
            KeyError: If no match is found.
        """
        for node in self.iter(recursive=self.recursive):
            if node.name == search or hash(node) == search:
                if node.path.is_dir():
                    shutil.rmtree(node.path)
                else:
                    node.path.unlink()
                return
        raise KeyError(f"No node {search} in the directory {self.path}")

    # -- Path join (mirrors pathlib) --

    def __truediv__(self, other: Union[str, Path, FileSystemNode]) -> FileSystemNode:
        """Join the directory path with *other*.

        Args:
            other: A string, Path, or FileSystemNode to append.

        Returns:
            A File or Directory for the resulting path.

        Raises:
            TypeError: If *other* has an unsupported type.
        """
        if isinstance(other, str):
            path = self.path / other
        elif isinstance(other, Path):
            path = self.path / other
        elif isinstance(other, (Directory, File)):
            path = self.path / other.name
        else:
            raise TypeError(f"Unsupported type {type(other)} for concatenation.")
        if path.is_dir():
            return Directory(path)
        elif path.is_file():
            return File(path)

    # -- Named methods replacing operators --

    def merge(self, other: "Directory") -> "Directory":
        """Merge *other* into this directory, then delete *other*.

        Moves all contents from *other* into this directory
        and removes the now-empty *other* directory.

        Args:
            other: The directory to merge from.

        Returns:
            This directory.
        """
        for item in other:
            item.path.rename(self.path / item.name)
        other.path.rmdir()
        return self

    def mkdir(self, name: str) -> "Directory":
        """Create a subdirectory.

        Args:
            name: Name of the subdirectory to create.

        Returns:
            A Directory instance for the new subdirectory.
        """
        new_dir = self.path / name
        new_dir.mkdir()
        return Directory(new_dir)

    def intersection(self, other: "Directory") -> set:
        """Return the set intersection of directory contents by name.

        Args:
            other: The other directory.

        Returns:
            Set of nodes present in both directories.
        """
        return set(self.iter(recursive=self.recursive)) & set(
            other.iter(other.recursive)
        )

    def union(self, other: "Directory") -> set:
        """Return the set union of directory contents by name.

        Args:
            other: The other directory.

        Returns:
            Set of all nodes from both directories.
        """
        return set(self) | set(other)

    # -- Public methods --

    def iter(
        self, recursive: bool = False, hidden: bool = False
    ) -> Iterator[FileSystemNode]:
        """Yield FileSystemNode instances for directory contents.

        Args:
            recursive: If True, recurse into subdirectories.
            hidden: If True, include dotfiles/dotdirs.

        Yields:
            File or Directory instances.

        Raises:
            RuntimeError: If the directory cannot be read.
        """
        try:
            nodes_iterator = self.path.rglob("*") if recursive else self.path.iterdir()
            for node_path in nodes_iterator:
                if not hidden and node_path.name.startswith("."):
                    continue
                try:
                    if node_path.is_file():
                        yield File(node_path)
                    elif node_path.is_dir():
                        yield Directory(node_path)
                except (FileNotFoundError, ValueError) as e:
                    raise ValueError(f"Error processing {node_path}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Error accessing contents of {self.path}: {e}") from e

    def iter_dir(
        self, recursive: bool = False, hidden: bool = False
    ) -> Iterator["Directory"]:
        """Yield only Directory children.

        Args:
            recursive: If True, recurse into subdirectories.
            hidden: If True, include hidden directories.

        Yields:
            Directory instances.
        """
        for node in self.iter(recursive=recursive, hidden=hidden):
            if node.is_instance(Directory):
                yield node

    def iter_files(
        self, recursive: bool = False, hidden: bool = False
    ) -> Iterator[File]:
        """Yield only File children.

        Args:
            recursive: If True, recurse into subdirectories.
            hidden: If True, include hidden files.

        Yields:
            File instances.
        """
        for node in self.iter(recursive=recursive, hidden=hidden):
            if node.is_instance(File):
                yield node

    def get_size(self) -> int:
        """Return total size of all contained files.

        Returns:
            Size in bytes.
        """
        if self.size is None:
            self.size = sum(file.get_size() for file in self.iter_files())
        return self.size

    def get_type(self) -> FileType:
        """Determine directory type by majority file type.

        Returns:
            The most common FileType among contained files.
        """
        files = list(self.iter_files(recursive=True))
        extension_to_ignore = (
            [None, "", ".DS_Store"]
            + FileTypeExtensions.OTHER.value
            + FileTypeExtensions.IMAGE.value
            + FileTypeExtensions.DOCUMENT.value
        )
        files_to_ignore = [f for f in files if f.extension in extension_to_ignore]
        files = [f for f in files if f not in files_to_ignore]
        file_types = Counter([f.get_type() for f in files])
        if file_types:
            return max(file_types, key=file_types.get)
        return FileType.OTHER

    def count(self) -> int:
        """Return the number of direct children.

        Returns:
            Child count.
        """
        return sum(1 for _ in self.iter(recursive=False))

    def count_dirs(self) -> int:
        """Return the number of direct subdirectories.

        Returns:
            Subdirectory count.
        """
        return sum(1 for _ in self.iter_dir(recursive=False))

    def count_files(self) -> int:
        """Return the number of direct child files.

        Returns:
            File count.
        """
        return sum(1 for _ in self.iter_files(recursive=False))

    def delete(self, recursive=False) -> None:
        """Delete the directory.

        Args:
            recursive: If True, remove contents recursively.
        """
        if recursive is True:
            shutil.rmtree(self.path)
        else:
            self.path.rmdir()

    def unpack(
        self,
        clean: bool = False,
        file_only: bool = False,
        dir_only: bool = False,
    ) -> set[FileSystemNode]:
        """Move contents to the parent directory.

        Args:
            clean: If True, clean node names before moving.
            file_only: If True, only move files.
            dir_only: If True, only move subdirectories.

        Returns:
            Set of nodes that were unpacked.
        """
        unpacked = set[FileSystemNode]()
        for node in self:
            if file_only and node.is_instance(Directory):
                continue
            if dir_only and node.is_instance(File):
                continue
            if clean:
                node.clean_name()
            node.move(self.path.parent / node.name)
            unpacked.add(node)
        if not os.listdir(self.path):
            self.delete()
        return unpacked
