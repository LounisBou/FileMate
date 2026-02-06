"""Sorting engine that organizes nodes into categorized directories."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional

from pydevmate import LogIt

from filemate.config import AppSettings
from filemate.directory import Directory
from filemate.file import File
from filemate.file_system_node import FileSystemNode
from filemate.file_type import FileType
from filemate.node_name_cleaner import NodeNameCleaner
from filemate.sorting_strategies import (
    DefaultStrategy,
    MovieStrategy,
    SortingStrategy,
    TVShowStrategy,
    find_matching_directory,
)


@dataclass
class Sorter:
    """Sort filesystem nodes into categorized directories based on type.

    Attributes:
        root_node: The root directory to sort.
        verbose: If True, emit verbose log output.
        dry_run: If True, log actions without performing them.
        settings: Application settings (optional, falls back to env vars).
        sorted_dir_names: Mapping of FileType to destination dir name.
        allowed_types: Mapping of FileType to list of additionally allowed types.
        logger: Logger instance.
        name_cleaner: NodeNameCleaner for metadata extraction.
    """

    STRATEGIES: ClassVar[dict[FileType, type[SortingStrategy]]] = {
        FileType.MOVIE: MovieStrategy,
        FileType.TVSHOW: TVShowStrategy,
    }

    root_node: FileSystemNode = field(init=True)
    verbose: bool = field(init=True, default=False)
    dry_run: bool = field(init=True, default=False)
    settings: Optional[AppSettings] = field(init=True, default=None)
    sorted_dir_names: dict = field(init=False, default_factory=dict)
    allowed_types: dict = field(init=False, default_factory=dict)
    logger: LogIt = field(init=True, default_factory=LogIt)
    name_cleaner: NodeNameCleaner = field(init=False, default=None)

    def __post_init__(self):
        """Load sorted directory names and allowed types."""
        if self.name_cleaner is None:
            self.name_cleaner = NodeNameCleaner(self.settings)
        self.__defined_sorted_dir()
        self.__defined_allowed_types()

    # -- Private methods --

    def __defined_sorted_dir(self) -> None:
        """Load sorted directory names from settings or environment."""
        if self.settings is not None:
            self.sorted_dir_names = {
                FileType.MOVIE: self.settings.movie_dir,
                FileType.TVSHOW: self.settings.tvshow_dir,
                FileType.EBOOK: self.settings.ebook_dir,
                FileType.AUDIO: self.settings.audio_dir,
                FileType.APP: self.settings.app_dir,
                FileType.IMAGE: self.settings.image_dir,
                FileType.ISO: self.settings.iso_dir,
                FileType.ANDROID: self.settings.android_dir,
                FileType.SCRIPT: self.settings.script_dir,
            }
        else:
            self.sorted_dir_names = {
                FileType.MOVIE: os.getenv("MOVIE_DIR"),
                FileType.TVSHOW: os.getenv("TVSHOW_DIR"),
                FileType.EBOOK: os.getenv("EBOOK_DIR"),
                FileType.AUDIO: os.getenv("AUDIO_DIR"),
                FileType.APP: os.getenv("APP_DIR"),
                FileType.IMAGE: os.getenv("IMAGE_DIR"),
                FileType.ISO: os.getenv("ISO_DIR"),
                FileType.ANDROID: os.getenv("ANDROID_DIR"),
                FileType.SCRIPT: os.getenv("SCRIPT_DIR"),
            }

    def __defined_allowed_types(self) -> None:
        """Define which extra types are allowed in each sorted directory."""
        self.allowed_types = {
            FileType.MOVIE: [FileType.SUBTITLE],
            FileType.TVSHOW: [FileType.MOVIE, FileType.SUBTITLE],
            FileType.EBOOK: [],
            FileType.AUDIO: [],
            FileType.APP: [],
            FileType.IMAGE: [],
            FileType.ISO: [],
            FileType.ANDROID: [],
            FileType.SCRIPT: [],
        }

    def __check_node_type(self, node: FileSystemNode) -> FileType | None:
        """Check if the node type is allowed for sorting.

        Args:
            node: The node to check.

        Returns:
            The FileType if allowed, None otherwise.
        """
        node_type = node.get_type()
        if node_type not in self.allowed_types:
            self.logger.warning(f"File type {node_type} is not allowed.")
            return None
        if node_type not in self.sorted_dir_names:
            self.logger.warning(f"No sorted directory for file type {node_type}")
            return None
        return node_type

    def __is_sorted_dir(self, node: FileSystemNode) -> bool:
        """Check if *node* is already a sorted directory.

        Args:
            node: The node to check.

        Returns:
            True if the node is one of the configured sorted directories.
        """
        if not node.is_instance(Directory):
            return False
        return any(node.name == d for d in self.sorted_dir_names.values())

    def __get_sorted_dir_node(self, node: FileSystemNode) -> FileSystemNode:
        """Get the sorted directory node for a given file type.

        Args:
            node: The node whose type determines the sorted directory.

        Returns:
            The sorted Directory node.
        """
        file_type = node.get_type()
        sorted_dir_name = self.sorted_dir_names[file_type]
        return self.root_node / sorted_dir_name

    def _get_strategy(self, file_type: FileType) -> SortingStrategy:
        """Look up the sorting strategy for a file type.

        Args:
            file_type: The file type to look up.

        Returns:
            An instance of the matching SortingStrategy.
        """
        strategy_cls = self.STRATEGIES.get(file_type, DefaultStrategy)
        return strategy_cls()

    def __get_node_destination_path(self, node: FileSystemNode) -> Path | None:
        """Compute the destination path for a node.

        Uses the strategy pattern to dispatch based on file type. For movie
        directories, also handles renaming in non-dry-run mode.

        Args:
            node: The node to get the destination path for.

        Returns:
            The destination Path, or None if the sorted directory is missing.
        """
        sorted_dir = self.__get_sorted_dir_node(node)
        node_type = node.get_type()

        if sorted_dir is None:
            self.logger.warning(
                f"Sorted directory for type {node_type.value} does not exist."
            )
            return None

        strategy = self._get_strategy(node_type)

        # Movie directories need special rename handling
        if node_type == FileType.MOVIE and node.is_instance(Directory):
            year = self.name_cleaner.get_year_from_node_name(node.stem_cleaned)
            if year is not None:
                folder_name = (
                    f"{self.name_cleaner.get_name_without_year(node.stem_cleaned)} ({year})"
                )
            else:
                folder_name = node.stem_cleaned

            match = find_matching_directory(
                folder_name, sorted_dir.path, self.name_cleaner, respect_year=True
            )
            if match is not None:
                return match.parent

            if not self.dry_run:
                node.rename(folder_name.capitalize())
            else:
                self.logger.warning(
                    f"Renaming movie dir to : {folder_name.capitalize()}"
                )
            return sorted_dir.path

        # For movie files and all other types, use strategy
        if node_type == FileType.MOVIE and node.is_instance(File):
            return strategy.get_destination(node, sorted_dir.path, self.name_cleaner)

        if node_type == FileType.TVSHOW:
            return strategy.get_destination(node, sorted_dir.path, self.name_cleaner)

        return strategy.get_destination(node, sorted_dir.path, self.name_cleaner)

    def __get_node_elements_to_sort(
        self, node: FileSystemNode, node_type: FileType
    ) -> list[FileSystemNode] | None:
        """Get the child elements of a node that need sorting.

        Args:
            node: The node to inspect.
            node_type: The determined type.

        Returns:
            List of child nodes to sort, or None if the node itself should be sorted.
        """
        if node.is_instance(File):
            return None
        if node_type == FileType.TVSHOW:
            return [
                child for child in node if child.get_type() == FileType.TVSHOW
            ]
        return None

    # -- Public methods --

    def set_allowed_types(
        self, file_type: FileType, allowed_types: list[FileType]
    ) -> None:
        """Set the allowed types for a file type.

        Args:
            file_type: The file type to configure.
            allowed_types: The allowed types for that file type.
        """
        self.allowed_types[file_type] = allowed_types

    def sort(
        self, node: FileSystemNode, delete_remaining_element: bool = False
    ) -> None:
        """Sort a single node into its destination directory.

        Args:
            node: The node to sort.
            delete_remaining_element: If True, delete leftovers after sorting.
        """
        if self.__is_sorted_dir(node):
            return

        self.logger.separator()
        self.logger.show(f"Sorting node: {node}")

        node_type = self.__check_node_type(node)
        if node_type is None:
            return

        self.logger.info(f"Node type: {node_type}")

        sorted_dir = node.parent.joinpath(self.sorted_dir_names[node_type])
        destination_path = self.__get_node_destination_path(node)
        if destination_path is None:
            return

        self.logger.info(f"Cleaned node name: {node.name_cleaned}")
        self.logger.info(f"Sorted directory: {sorted_dir}")
        self.logger.info(f"Destination path: {destination_path}")

        elements = self.__get_node_elements_to_sort(node, node_type)
        if elements is not None:
            for element in elements:
                self.logger.success(
                    f"Node to sort: [{element.__class__.__name__}] "
                    f"{destination_path / element.name_cleaned}"
                )
                if not self.dry_run:
                    element.move(destination_path / element.name_cleaned)
            if delete_remaining_element:
                self.logger.warning(f"Deleting remaining element: {node}")
                if not self.dry_run:
                    node.delete(recursive=True)
        else:
            self.logger.success(
                f"Node to sort: [{node.__class__.__name__}] "
                f"{destination_path / node.name_cleaned}"
            )
            if not self.dry_run:
                node.move(destination_path / node.name_cleaned)

    def process(self, delete_remaining_element: bool = False) -> None:
        """Sort all children of the root node.

        Args:
            delete_remaining_element: If True, delete leftovers after sorting.

        Raises:
            ValueError: If the root node is neither a File nor a Directory.
        """
        if self.root_node.is_instance(File):
            if self.verbose:
                self.logger.show(f"Sorting file: {self.root_node.name_cleaned}")
            self.sort(self.root_node)
            return

        if self.root_node.is_instance(Directory):
            if self.verbose:
                self.logger.show(
                    f"Sorting directory: {self.root_node.name_cleaned}"
                )
            for node in self.root_node:
                if self.verbose:
                    self.logger.show(f"Sorting child node: {node.name_cleaned}")
                self.sort(node, delete_remaining_element)
            return

        raise ValueError(f"Node type {self.root_node} is not allowed.")
