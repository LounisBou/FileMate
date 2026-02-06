"""Tests for the Directory class."""
import pytest

from filemate.directory import Directory
from filemate.file import File
from filemate.file_type import FileType


def test_directory_creation(tmp_path, env_setup):
    """Directory attributes are populated on creation."""
    d = tmp_path / "testdir"
    d.mkdir()
    node = Directory(d)
    assert node.name == "testdir"
    assert node.path == d.resolve()


def test_directory_not_a_file(tmp_path, env_setup):
    """ValueError when path is a file, not a directory."""
    f = tmp_path / "afile.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        Directory(f)


def test_directory_year_extraction(tmp_path, env_setup):
    """Year is extracted from directory name."""
    d = tmp_path / "Movie (2020)"
    d.mkdir()
    node = Directory(d)
    assert node.year == 2020


def test_directory_iter(sample_dir):
    """Iteration yields File and Directory objects."""
    node = Directory(sample_dir)
    items = list(node.iter())
    assert len(items) == 3
    types = {type(item) for item in items}
    assert File in types


def test_directory_iter_files(sample_dir):
    """iter_files yields only File objects."""
    node = Directory(sample_dir)
    files = list(node.iter_files())
    for f in files:
        assert isinstance(f, File)
    assert len(files) == 3


def test_directory_iter_dirs(tmp_path, env_setup):
    """iter_dirs yields only Directory objects."""
    d = tmp_path / "parent"
    d.mkdir()
    (d / "child_dir").mkdir()
    (d / "file.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    dirs = list(node.iter_dir())
    assert len(dirs) == 1
    assert all(isinstance(item, Directory) for item in dirs)


def test_directory_contains(tmp_path, env_setup):
    """File membership check works."""
    d = tmp_path / "container"
    d.mkdir()
    (d / "inside.txt").write_text("x", encoding="utf-8")
    dir_node = Directory(d)
    file_node = File(d / "inside.txt")
    assert file_node in dir_node


def test_directory_getitem(tmp_path, env_setup):
    """Subscript access by filename works."""
    d = tmp_path / "lookup"
    d.mkdir()
    (d / "target.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    found = node["target.txt"]
    assert found.name == "target.txt"


def test_directory_getitem_missing(tmp_path, env_setup):
    """KeyError for missing item."""
    d = tmp_path / "lookup2"
    d.mkdir()
    node = Directory(d)
    with pytest.raises(KeyError):
        node["nonexistent.txt"]


def test_directory_count(sample_dir):
    """count, count_files, count_dirs return correct values."""
    node = Directory(sample_dir)
    assert node.count() == 3
    assert node.count_files() == 3
    assert node.count_dirs() == 0


def test_directory_truediv(tmp_path, env_setup):
    """dir / 'name' returns path-joined result."""
    d = tmp_path / "base"
    d.mkdir()
    (d / "child.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    result = node / "child.txt"
    assert isinstance(result, File)
    assert result.name == "child.txt"


def test_directory_mod_mkdir(tmp_path, env_setup):
    """dir % 'sub' creates a subdirectory."""
    d = tmp_path / "parent_mod"
    d.mkdir()
    node = Directory(d)
    sub = node % "newsub"
    assert isinstance(sub, Directory)
    assert sub.path.exists()
    assert sub.name == "newsub"


def test_directory_get_type(tmp_path, env_setup):
    """Directory type is determined by majority file type."""
    d = tmp_path / "typed"
    d.mkdir()
    for name in ("first film.mp4", "second film.mp4", "third film.mp4"):
        (d / name).write_bytes(b"\x00" * 10)
    (d / "song.mp3").write_bytes(b"\x00" * 10)
    node = Directory(d)
    assert node.get_type() == FileType.MOVIE


def test_directory_delete_empty(tmp_path, env_setup):
    """Empty directory is deleted."""
    d = tmp_path / "to_delete"
    d.mkdir()
    node = Directory(d)
    node.delete()
    assert not d.exists()


def test_directory_delete_recursive(tmp_path, env_setup):
    """Non-empty directory is deleted with recursive=True."""
    d = tmp_path / "to_delete_r"
    d.mkdir()
    (d / "file.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    node.delete(recursive=True)
    assert not d.exists()


def test_directory_unpack(tmp_path, env_setup):
    """Contents are moved to parent directory."""
    parent = tmp_path / "parent_unpack"
    parent.mkdir()
    inner = parent / "inner"
    inner.mkdir()
    (inner / "file.txt").write_text("x", encoding="utf-8")
    node = Directory(inner)
    node.unpack()
    assert (parent / "file.txt").exists()
    assert not inner.exists()
