"""File node representing a single file in the filesystem."""

from dataclasses import dataclass, field

from filemate.file_system_node import FileSystemNode
from filemate.file_type import FileType
from filemate.file_type_extensions import FileTypeExtensions


@dataclass(eq=False)
class File(FileSystemNode):
    """A filesystem node representing a single file.

    Attributes:
        extension: The file extension (without leading dot), lowercased.
    """

    extension: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Initialize file-specific attributes after dataclass init.

        Raises:
            ValueError: If the path is not a file.
        """
        super().__post_init__()
        if not self.path.is_file():
            raise ValueError(f"The path {self.path} is not a file.")
        self.extension = self.path.suffix[1:].lower()
        self.modification_time = self.path.stat().st_mtime

    def __str__(self) -> str:
        """Return a short string representation."""
        return f"File: {self.path.name}"

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return (
            f"File: {self.path}\n"
            f"Name: {self.name}\n"
            f"Cleaned Name: {self.name_cleaned}\n"
            f"Stem: {self.stem}\n"
            f"Cleaned Stem: {self.stem_cleaned}\n"
            f"Extension: {self.extension}\n"
            f"Size: {self.human_readable_size()}\n"
            f"Last Modified: {self.formatted_modification_time()}\n"
            f"Type: {self.get_type()}"
        )

    def __contains__(self, item: str) -> bool:
        """Check if a string is contained in the file stem.

        Args:
            item: The string to search for.

        Returns:
            True if the string is found in the file stem.
        """
        return item in self.stem

    def get_size(self) -> int:
        """Return the file size in bytes, reading from disk if needed.

        Returns:
            The file size in bytes.
        """
        if self.size is None:
            self.size = self.path.stat().st_size
        return self.size

    def get_type(self) -> FileType:
        """Determine the semantic file type based on extension.

        VIDEO extensions are further classified as MOVIE or TVSHOW
        depending on whether season/episode info is found in the name.

        Returns:
            The determined FileType.
        """
        file_type_ext = FileTypeExtensions.get_file_type(self.extension)

        if file_type_ext is None:
            return FileType.OTHER

        if file_type_ext.name == FileTypeExtensions.VIDEO.name:
            season, episode = self.name_cleaner.get_season_and_episode_from_node_name(self.stem)
            if season is not None or episode is not None:
                return FileType.TVSHOW
            else:
                return FileType.MOVIE

        if not hasattr(FileType, file_type_ext.name):
            return FileType.OTHER

        return FileType[file_type_ext.name]

    def delete(self, recursive=False) -> None:
        """Delete the file from disk."""
        self.path.unlink()

    def pack(self, includes: set[FileSystemNode] = None) -> str:
        """Pack the file into a same-named directory.

        Creates a directory with the file's stem name, moves the file
        into it, and optionally moves additional nodes.

        Args:
            includes: Additional nodes to include in the pack directory.

        Returns:
            The path to the created pack directory.
        """
        directory = self.path.parent / self.stem
        directory.mkdir(exist_ok=True)
        self.move(directory / self.path.name)
        if includes is not None:
            for node in includes:
                node.move(directory / node.path.name)
        return directory
    