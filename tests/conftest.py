"""Fixtures and configuration for pytest."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from filemate.file_system_node import FileSystemNode
from filemate.node_name_cleaner import NodeNameCleaner


@pytest.fixture()
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture()
def env_setup(monkeypatch, project_root):
    """Set env vars pointing to the real cleaning config files."""
    monkeypatch.setenv("CLEAN_CHARACTERS_FILE", "clean_chars.txt")
    monkeypatch.setenv("CLEAN_WORDS_FILE", "clean_words.txt")


@pytest.fixture(autouse=True)
def setup_cleaner(env_setup):
    """Set the shared NodeNameCleaner for all tests (autouse).

    Creates a NodeNameCleaner using the env vars and installs it as the
    shared cleaner on FileSystemNode. Resets after the test.
    """
    cleaner = NodeNameCleaner()
    FileSystemNode.set_name_cleaner(cleaner)
    yield cleaner
    FileSystemNode._shared_cleaner = None


@pytest.fixture()
def sorter_env_setup(monkeypatch, env_setup):
    """Set all sorted directory env vars needed by Sorter."""
    monkeypatch.setenv("MOVIE_DIR", "001-MOVIES")
    monkeypatch.setenv("TVSHOW_DIR", "002-TVSHOWS")
    monkeypatch.setenv("EBOOK_DIR", "003-EBOOKS")
    monkeypatch.setenv("AUDIO_DIR", "004-AUDIO")
    monkeypatch.setenv("APP_DIR", "005-APPS")
    monkeypatch.setenv("ANDROID_DIR", "006-ANDROID")
    monkeypatch.setenv("IMAGE_DIR", "007-IMAGES")
    monkeypatch.setenv("ISO_DIR", "008-ISO")
    monkeypatch.setenv("SCRIPT_DIR", "099-SCRIPTS")


@pytest.fixture()
def sample_file(tmp_path, env_setup):
    """Create a temporary sample file and return its Path."""
    f = tmp_path / "sample.txt"
    f.write_text("hello world", encoding="utf-8")
    return f


@pytest.fixture()
def sample_dir(tmp_path, env_setup):
    """Create a temporary directory with sample files and return its Path."""
    d = tmp_path / "sample_dir"
    d.mkdir()
    (d / "file1.txt").write_text("content1", encoding="utf-8")
    (d / "file2.mp4").write_bytes(b"\x00" * 100)
    (d / "file3.mp3").write_bytes(b"\x00" * 50)
    return d


@pytest.fixture()
def name_cleaner(setup_cleaner):
    """Return the shared NodeNameCleaner instance."""
    return setup_cleaner


def _noop_cache_decorator(*args, **kwargs):
    """No-op replacement for CacheIt decorator."""
    def decorator(func):
        return func
    # Handle both @CacheIt and @CacheIt(...) usage
    if args and callable(args[0]):
        return args[0]
    return decorator


@pytest.fixture()
def mock_redis():
    """Patch pydevmate.CacheIt and SaveIt so tests don't need Redis."""
    mock_saveit_cls = MagicMock()
    mock_saveit_cls.return_value = MagicMock()

    with (
        patch("pydevmate.CacheIt", side_effect=_noop_cache_decorator),
        patch("pydevmate.SaveIt", mock_saveit_cls),
        patch("filemate.file_system_node_tree.CacheIt", side_effect=_noop_cache_decorator),
        patch("filemate.file_system_node_tree.SaveIt", mock_saveit_cls),
        patch("filemate.file_system_node_tree.TimeIt", side_effect=_noop_cache_decorator),
    ):
        yield mock_saveit_cls


@pytest.fixture()
def tree_setup(tmp_path, env_setup, mock_redis):
    """Create a directory structure and return a FileSystemNodeTree."""
    from filemate.directory import Directory
    from filemate.file_system_node_tree import FileSystemNodeTree

    root = tmp_path / "tree_root"
    root.mkdir()
    (root / "file_a.txt").write_text("aaa", encoding="utf-8")
    (root / "file_b.mp4").write_bytes(b"\x00" * 100)
    sub = root / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("nested", encoding="utf-8")

    root_node = Directory(root)
    tree = FileSystemNodeTree(root_node)
    tree.build()
    return tree
