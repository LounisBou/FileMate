"""Factory for creating File or Directory nodes from a path."""

from pathlib import Path

from filemate.directory import Directory
from filemate.file import File
from filemate.file_system_node import FileSystemNode


class FileSystemNodeFactory:
    """Create FileSystemNode instances based on path type."""

    @classmethod
    def create_node(cls, path: Path) -> FileSystemNode:
        """Create a File or Directory node from a filesystem path.

        Args:
            path: Path to inspect.

        Returns:
            A File or Directory instance.

        Raises:
            ValueError: If the path is neither a file nor a directory.
        """
        if path.is_file():
            return File(path)
        elif path.is_dir():
            return Directory(path)
        else:
            raise ValueError(f"The path {path} is not a file or directory.")
