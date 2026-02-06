"""Sorting strategies for placing nodes into destination directories."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from filemate.file_system_node import FileSystemNode
from filemate.node_name_cleaner import NodeNameCleaner


def _tokenize_for_matching(name: str, cleaner: NodeNameCleaner) -> set[str]:
    """Lowercase a name, strip year, and split into a set of tokens.

    Args:
        name: The directory or file name to tokenize.
        cleaner: NodeNameCleaner used for year stripping.

    Returns:
        A set of lowercase token strings (empty tokens excluded).
    """
    name = name.lower().strip()
    name = cleaner.get_name_without_year(name)
    name = re.sub(r"[()]", " ", name)
    tokens = name.split()
    return {t for t in tokens if t}


def find_matching_directory(
    candidate_name: str,
    sorted_dir_path: Path,
    cleaner: NodeNameCleaner,
    respect_year: bool = False,
) -> Optional[Path]:
    """Find an existing subdirectory that fuzzy-matches *candidate_name*.

    Uses bidirectional token containment: if all tokens of one name appear
    in the other, it counts as a match.  Single-token overlaps require
    exact set equality to avoid false positives.

    Args:
        candidate_name: The computed folder name for the node being sorted.
        sorted_dir_path: The type-specific sorted directory (e.g. ``002-TVSHOWS``).
        cleaner: NodeNameCleaner for year extraction.
        respect_year: When True, skip matches where both names have different years.

    Returns:
        The Path of the best matching existing subdirectory, or None.
    """
    if not sorted_dir_path.is_dir():
        return None

    candidate_tokens = _tokenize_for_matching(candidate_name, cleaner)
    if not candidate_tokens:
        return None

    candidate_year = cleaner.get_year_from_node_name(candidate_name.lower())

    best_path: Optional[Path] = None
    best_overlap = 0
    best_token_diff = float("inf")

    for entry in sorted_dir_path.iterdir():
        if not entry.is_dir():
            continue

        dir_tokens = _tokenize_for_matching(entry.name, cleaner)
        if not dir_tokens:
            continue

        # Year conflict check
        if respect_year:
            dir_year = cleaner.get_year_from_node_name(entry.name.lower())
            if candidate_year is not None and dir_year is not None:
                if candidate_year != dir_year:
                    continue

        # Bidirectional token containment
        if not (dir_tokens <= candidate_tokens or candidate_tokens <= dir_tokens):
            continue

        overlap = len(dir_tokens & candidate_tokens)

        # Single-token overlaps require exact set equality
        if overlap < 2 and dir_tokens != candidate_tokens:
            continue

        # Pick best match: highest overlap, tiebreak by closest token count
        token_diff = abs(len(dir_tokens) - len(candidate_tokens))
        if overlap > best_overlap or (overlap == best_overlap and token_diff < best_token_diff):
            best_overlap = overlap
            best_token_diff = token_diff
            best_path = entry

    return best_path


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

        match = find_matching_directory(folder_name, sorted_dir_path, cleaner, respect_year=True)
        if match is not None:
            return match

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

        match = find_matching_directory(show_name, sorted_dir_path, cleaner)
        if match is not None:
            return match

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
