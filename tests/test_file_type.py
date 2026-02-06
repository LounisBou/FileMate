"""Tests for FileType enum."""
from filemate.file_type import FileType


def test_filetype_members_exist():
    """All 14 enum members are accessible."""
    expected = [
        "VIDEO", "MOVIE", "TVSHOW", "EBOOK", "AUDIO", "APP", "ANDROID",
        "ARCHIVE", "IMAGE", "SUBTITLE", "DOCUMENT", "ISO", "SCRIPT", "OTHER",
    ]
    for name in expected:
        assert hasattr(FileType, name), f"Missing member: {name}"


def test_filetype_values_are_lowercase_strings():
    """Each member's value is a lowercase string."""
    for member in FileType:
        assert isinstance(member.value, str)
        assert member.value == member.value.lower()
