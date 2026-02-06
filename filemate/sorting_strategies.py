"""Sorting strategies for placing nodes into destination directories."""

from abc import ABC, abstractmethod
from pathlib import Path

from filemate.file_system_node import FileSystemNode
from filemate.node_name_cleaner import NodeNameCleaner


class SortingStrategy(ABC):
    """Base class for sorting strategies.

    Each strategy decides where a node should be placed within a sorted
    directory based on its metadata.
    """

    @abstractmethod
    def get_destination(
        self,
        node: FileSystemNode,
        sorted_dir_path: Path,
        cleaner: NodeNameCleaner,
    ) -> Path:
        """Compute the destination path for a node.

        Args:
            node: The node to sort.
            sorted_dir_path: The root sorted directory for this file type.
            cleaner: The NodeNameCleaner for extracting metadata.

        Returns:
            The destination Path.
        """
        raise NotImplementedError


class MovieStrategy(SortingStrategy):
    """Place movies in a ``Title (Year)/`` subfolder."""

    def get_destination(
        self,
        node: FileSystemNode,
        sorted_dir_path: Path,
        cleaner: NodeNameCleaner,
    ) -> Path:
        """Return ``sorted_dir/Title (Year)`` or ``sorted_dir/Title``.

        Args:
            node: The movie node.
            sorted_dir_path: Path to the movies sorted directory.
            cleaner: NodeNameCleaner for metadata extraction.

        Returns:
            Destination path.
        """
        year = cleaner.get_year_from_node_name(node.stem_cleaned)
        if year is not None:
            folder_name = f"{cleaner.get_name_without_year(node.stem_cleaned)} ({year})"
        else:
            folder_name = node.stem_cleaned
        return sorted_dir_path / folder_name.capitalize()


class TVShowStrategy(SortingStrategy):
    """Place TV shows in a ``Show Name/`` subfolder."""

    def get_destination(
        self,
        node: FileSystemNode,
        sorted_dir_path: Path,
        cleaner: NodeNameCleaner,
    ) -> Path:
        """Return ``sorted_dir/Show Name``.

        Args:
            node: The TV show node.
            sorted_dir_path: Path to the TV shows sorted directory.
            cleaner: NodeNameCleaner for metadata extraction.

        Returns:
            Destination path.
        """
        show_name = cleaner.get_name_without_season_and_episode(node.stem_cleaned)
        show_name = cleaner.get_name_without_year(show_name)
        return sorted_dir_path / show_name.capitalize()


class DefaultStrategy(SortingStrategy):
    """Place nodes directly in the type directory (flat)."""

    def get_destination(
        self,
        node: FileSystemNode,
        sorted_dir_path: Path,
        cleaner: NodeNameCleaner,
    ) -> Path:
        """Return *sorted_dir_path* unchanged.

        Args:
            node: The node to sort.
            sorted_dir_path: Path to the type-specific sorted directory.
            cleaner: NodeNameCleaner (unused for default strategy).

        Returns:
            The sorted directory path itself.
        """
        return sorted_dir_path
