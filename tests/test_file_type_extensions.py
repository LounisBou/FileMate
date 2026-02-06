"""Tests for FileTypeExtensions enum."""
from filemate.file_type_extensions import FileTypeExtensions


def test_get_file_type_video():
    """Common video extensions resolve to VIDEO."""
    for ext in ("avi", "mkv", "mp4"):
        result = FileTypeExtensions.get_file_type(ext)
        assert result == FileTypeExtensions.VIDEO, f"{ext} should be VIDEO, got {result}"


def test_get_file_type_audio():
    """Audio extensions resolve to AUDIO (regression test for overlap fix)."""
    for ext in ("mp3", "wav", "flac", "ogg", "m4a", "aac"):
        result = FileTypeExtensions.get_file_type(ext)
        assert result == FileTypeExtensions.AUDIO, f"{ext} should be AUDIO, got {result}"


def test_get_file_type_ebook():
    """Ebook extensions resolve to EBOOK."""
    for ext in ("pdf", "epub", "mobi"):
        result = FileTypeExtensions.get_file_type(ext)
        assert result == FileTypeExtensions.EBOOK, f"{ext} should be EBOOK, got {result}"


def test_get_file_type_unknown():
    """Unknown extensions return None."""
    assert FileTypeExtensions.get_file_type("xyz") is None
    assert FileTypeExtensions.get_file_type("randomext") is None


def test_get_file_type_case_insensitive():
    """Extension lookup is case-insensitive."""
    assert FileTypeExtensions.get_file_type("MP3") == FileTypeExtensions.AUDIO
    assert FileTypeExtensions.get_file_type("Mp4") == FileTypeExtensions.VIDEO
    assert FileTypeExtensions.get_file_type("PDF") == FileTypeExtensions.EBOOK


def test_no_video_audio_overlap():
    """VIDEO and AUDIO extension lists must be disjoint (regression guard)."""
    video_set = set(FileTypeExtensions.VIDEO.value)
    audio_set = set(FileTypeExtensions.AUDIO.value)
    overlap = video_set & audio_set
    assert overlap == set(), f"VIDEO and AUDIO overlap on: {overlap}"


def test_types_returns_members():
    """types() returns all enum members as a dict."""
    members = FileTypeExtensions.types()
    assert "VIDEO" in members
    assert "AUDIO" in members
    assert "EBOOK" in members


def test_keys_returns_member_names():
    """keys() returns the names of all enum members."""
    keys = FileTypeExtensions.keys()
    assert "VIDEO" in keys
    assert "AUDIO" in keys
    assert "OTHER" in keys
