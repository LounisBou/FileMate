"""Filename cleaning utilities for removing unwanted characters and words."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from filemate.config import AppSettings


@dataclass
class NodeNameCleaner:
    """Clean filesystem node names by removing unwanted characters and words.

    Attributes:
        cleaning_chars_path: Path to the file containing characters to strip.
        cleaning_words_path: Path to the file containing words to strip.
        cleaning_chars: List of characters to remove from names.
        cleaning_words: List of words to remove from names.
    """

    cleaning_chars_path: Path | None = field(init=False, default=None)
    cleaning_words_path: Path | None = field(init=False, default=None)
    cleaning_chars: List[str] = field(init=False, default_factory=list)
    cleaning_words: List[str] = field(init=False, default_factory=list)

    def __init__(self, settings: Optional[AppSettings] = None) -> None:
        """Initialize the cleaner.

        Args:
            settings: Application settings. If None, falls back to
                environment variables for backward compatibility.
        """
        if settings is not None:
            self.cleaning_chars_path = settings.clean_characters_file
            self.cleaning_words_path = settings.clean_words_file
        else:
            main_script_dir = Path(__file__).parent.resolve().parent
            self.cleaning_chars_path = main_script_dir / os.getenv(
                "CLEAN_CHARACTERS_FILE", "clean_chars.txt"
            )
            self.cleaning_words_path = main_script_dir / os.getenv(
                "CLEAN_WORDS_FILE", "clean_words.txt"
            )
        self.__load_cleaning_chars()
        self.__load_cleaning_words()
        
    def __load_cleaning_chars(self) -> None:
        """Load the list of characters to strip from the config file."""
        with open(self.cleaning_chars_path, "r", encoding="utf-8") as file:
            self.cleaning_chars = file.read().splitlines()

    def __load_cleaning_words(self) -> None:
        """Load the list of words to strip from the config file."""
        with open(self.cleaning_words_path, "r", encoding="utf-8") as file:
            self.cleaning_words = file.read().splitlines()

    def __clean_node_stem_chars(self, node_stem: str, replacement: str = " ") -> str:
        """Replace unwanted characters in the node stem.

        Args:
            node_stem: Node name without extension.
            replacement: Replacement string for each unwanted character.

        Returns:
            The stem with unwanted characters replaced.
        """
        for char_to_clean in self.cleaning_chars:
            node_stem = node_stem.replace(char_to_clean, replacement)
        return node_stem

    def __clean_node_stem_words(self, node_stem: str, replacement: str = "") -> str:
        """Remove unwanted words from the node stem.

        Args:
            node_stem: Node name without extension.
            replacement: Replacement string for each unwanted word.

        Returns:
            The stem with unwanted words removed.
        """
        for word_to_clean in self.cleaning_words:
            node_stem = re.sub(rf"\b{word_to_clean}\b", replacement, node_stem)
        return node_stem.strip()

    def __clean_node_stem(self, node_stem: str) -> str:
        """Apply full cleaning pipeline to a node stem.

        Pipeline: lowercase, strip, remove chars, remove words,
        collapse whitespace, strip again.

        Args:
            node_stem: Raw node name without extension.

        Returns:
            The fully cleaned stem.
        """
        node_stem = node_stem.lower().strip()
        node_stem = self.__clean_node_stem_chars(node_stem)
        node_stem = self.__clean_node_stem_words(node_stem)
        node_stem = self.cleanup_extra_space(node_stem)
        return node_stem.strip()

    @staticmethod
    def cleanup_extra_space(node_name: str) -> str:
        """Collapse multiple whitespace characters into single spaces.

        Args:
            node_name: The name to clean.

        Returns:
            The name with extra whitespace removed.
        """
        return re.sub(r"\s+", " ", node_name)

    def get_cleaned_node_stem(self, path: Path) -> str:
        """Return the cleaned stem of a node path.

        For directories, the stem is the full name. For files, it is
        the name without extension.

        Args:
            path: The full path of the node.

        Returns:
            The cleaned stem string.
        """
        if path.is_dir():
            return self.__clean_node_stem(path.name)
        return self.__clean_node_stem(path.stem)

    def get_cleaned_node_name(self, path: Path) -> str:
        """Return the cleaned name of a node path, preserving extension.

        Args:
            path: The full path of the node.

        Returns:
            The cleaned name (with extension for files).
        """
        if path.is_dir():
            return self.__clean_node_stem(path.name)
        return self.__clean_node_stem(path.stem) + path.suffix

    def get_year_from_node_name(self, node_name: str) -> int | None:
        """Extract a year (19xx or 20xx) from a node name.

        Args:
            node_name: The name to parse.

        Returns:
            The year as an integer, or None if not found.
        """
        year = re.search(r"\b(19|20)\d{2}\b", node_name, flags=re.IGNORECASE)
        return int(year.group()) if year else None

    def get_season_and_episode_from_node_name(
        self, node_name: str
    ) -> tuple[int | None, int | None]:
        """Extract season and episode numbers from a node name.

        Recognizes patterns like s01e04, saison 1 episode 4, etc.

        Args:
            node_name: The name to parse.

        Returns:
            Tuple of (season, episode), either may be None.
        """
        pattern = (
            r"(?i)s(?:aison|eason)?\s*(\d{1,2})e(?:pisode)?\s*(\d{1,2})"
            r"|s(?:aison|eason)?\s*(\d{1,2})"
            r"|e(?:pisode)?\s*(\d{1,2})"
        )
        match = re.findall(pattern, node_name)

        season = None
        episode = None

        for groups in match:
            if groups[0] and groups[1]:
                season = int(groups[0])
                episode = int(groups[1])
                break
            elif groups[0]:
                season = int(groups[0])
            elif groups[1]:
                episode = int(groups[1])
            elif groups[2] and groups[3]:
                season = int(groups[2])
                episode = int(groups[3])
                break
            elif groups[2]:
                season = int(groups[2])
            elif groups[3]:
                episode = int(groups[3])

        return season, episode

    def get_name_without_year(self, node_name: str) -> str:
        """Remove year information from a node name.

        Args:
            node_name: The name to clean.

        Returns:
            The name with year patterns removed.
        """
        pattern_year = r"\b(19|20)\d{2}\b"
        cleaned_name = re.sub(pattern_year, "", node_name, flags=re.IGNORECASE).strip()
        return self.cleanup_extra_space(cleaned_name)

    def get_name_without_season_and_episode(self, node_name: str) -> str:
        """Remove season and episode information from a node name.

        Args:
            node_name: The name to clean.

        Returns:
            The name with season/episode patterns removed.
        """
        pattern_season = r"(?i)(?:\bs(?:aison|eason)?\s*\d{1,2})"
        pattern_episode = r"(?i)(?:\be(?:pisode)?\s*\d{1,2})"
        cleaned_name = re.sub(pattern_season, "", node_name, flags=re.IGNORECASE).strip()
        cleaned_name = re.sub(pattern_episode, "", cleaned_name, flags=re.IGNORECASE).strip()
        return self.cleanup_extra_space(cleaned_name)