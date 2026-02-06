"""Tests for FileSystemNodeFactory."""
import pytest

from filemate.file_system_node_factory import FileSystemNodeFactory
from filemate.file import File
from filemate.directory import Directory


def test_create_node_file(tmp_path, env_setup):
    """Factory returns File for a file path."""
    f = tmp_path / "test.txt"
    f.write_text("x", encoding="utf-8")
    node = FileSystemNodeFactory.create_node(f)
    assert isinstance(node, File)


def test_create_node_directory(tmp_path, env_setup):
    """Factory returns Directory for a dir path."""
    d = tmp_path / "testdir"
    d.mkdir()
    node = FileSystemNodeFactory.create_node(d)
    assert isinstance(node, Directory)


def test_create_node_nonexistent_raises(tmp_path):
    """ValueError for a path that is neither file nor directory."""
    with pytest.raises(ValueError, match="not a file or directory"):
        FileSystemNodeFactory.create_node(tmp_path / "ghost")
