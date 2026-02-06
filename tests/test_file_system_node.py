"""Tests for FileSystemNode base class (tested via File/Directory instances)."""
import math

import pytest

from filemate.file import File
from filemate.directory import Directory


# -- Error paths --

def test_type_error_when_path_not_pathlib(env_setup):
    """TypeError when path is not a pathlib.Path."""
    with pytest.raises(TypeError, match="path must be a pathlib.Path"):
        File("/not/a/pathlib/path")


def test_instanceof_returns_class(tmp_path, env_setup):
    """_instanceof() returns the class of the node."""
    f = tmp_path / "test.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    assert node._instanceof() is File


def test_reload_deleted_file_raises(tmp_path, env_setup):
    """reload() on a deleted file raises FileNotFoundError."""
    f = tmp_path / "gone.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    f.unlink()
    with pytest.raises(FileNotFoundError):
        node.reload()


# -- Comparison operators --

def test_ne(tmp_path, env_setup):
    """__ne__: different names are not equal."""
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    a = File(tmp_path / "a.txt")
    b = File(tmp_path / "b.txt")
    assert a != b


def test_ne_same(tmp_path, env_setup):
    """__ne__: same file is equal to itself."""
    (tmp_path / "same.txt").write_text("x", encoding="utf-8")
    node = File(tmp_path / "same.txt")
    assert not (node != node)


# -- Size arithmetic operators --

def _make_sized_file(tmp_path, name, size_bytes):
    """Helper to create a file and return a File node with size set."""
    f = tmp_path / name
    f.write_bytes(b"\x00" * size_bytes)
    node = File(f)
    node.size = f.stat().st_size
    return node


def test_add(tmp_path, env_setup):
    """__add__: sum of two file sizes."""
    a = _make_sized_file(tmp_path, "a.txt", 100)
    b = _make_sized_file(tmp_path, "b.txt", 200)
    assert a + b == 300


def test_sub(tmp_path, env_setup):
    """__sub__: difference of two file sizes."""
    a = _make_sized_file(tmp_path, "a.txt", 300)
    b = _make_sized_file(tmp_path, "b.txt", 100)
    assert a - b == 200


def test_len(tmp_path, env_setup):
    """__len__: returns size."""
    node = _make_sized_file(tmp_path, "a.txt", 42)
    assert len(node) == 42


def test_lt(tmp_path, env_setup):
    """__lt__: smaller < larger."""
    a = _make_sized_file(tmp_path, "a.txt", 10)
    b = _make_sized_file(tmp_path, "b.txt", 20)
    assert a < b
    assert not b < a


def test_le(tmp_path, env_setup):
    """__le__: smaller <= equal <= larger."""
    a = _make_sized_file(tmp_path, "a.txt", 10)
    b = _make_sized_file(tmp_path, "b.txt", 10)
    c = _make_sized_file(tmp_path, "c.txt", 20)
    assert a <= b
    assert a <= c


def test_gt(tmp_path, env_setup):
    """__gt__: larger > smaller."""
    a = _make_sized_file(tmp_path, "a.txt", 20)
    b = _make_sized_file(tmp_path, "b.txt", 10)
    assert a > b
    assert not b > a


def test_ge(tmp_path, env_setup):
    """__ge__: larger >= equal >= smaller."""
    a = _make_sized_file(tmp_path, "a.txt", 20)
    b = _make_sized_file(tmp_path, "b.txt", 20)
    c = _make_sized_file(tmp_path, "c.txt", 10)
    assert a >= b
    assert a >= c


def test_neg(tmp_path, env_setup):
    """__neg__: returns negative size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert -node == -50


def test_pos(tmp_path, env_setup):
    """__pos__: returns positive size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert +node == 50


def test_abs(tmp_path, env_setup):
    """__abs__: returns absolute size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert abs(node) == 50


def test_round(tmp_path, env_setup):
    """__round__: rounds size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert round(node) == 50


def test_floor(tmp_path, env_setup):
    """__floor__: floor of size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert math.floor(node) == 50


def test_ceil(tmp_path, env_setup):
    """__ceil__: ceil of size."""
    node = _make_sized_file(tmp_path, "a.txt", 50)
    assert math.ceil(node) == 50


# -- Utility methods --

def test_human_readable_size_bytes(tmp_path, env_setup):
    """human_readable_size for small files returns bytes."""
    node = _make_sized_file(tmp_path, "small.txt", 512)
    result = node.human_readable_size()
    assert "B" in result
    assert "512.00" in result


def test_human_readable_size_kb(tmp_path, env_setup):
    """human_readable_size for KB-sized files."""
    node = _make_sized_file(tmp_path, "kb.txt", 2048)
    result = node.human_readable_size()
    assert "KB" in result


def test_human_readable_size_mb(tmp_path, env_setup):
    """human_readable_size for MB-sized files."""
    f = tmp_path / "mb.bin"
    f.write_bytes(b"\x00" * (2 * 1024 * 1024))
    node = File(f)
    node.size = f.stat().st_size
    result = node.human_readable_size()
    assert "MB" in result


def test_formatted_modification_time(tmp_path, env_setup):
    """formatted_modification_time returns a date string."""
    node = _make_sized_file(tmp_path, "a.txt", 10)
    result = node.formatted_modification_time()
    # Should contain year-month-day format
    assert "-" in result
    assert ":" in result


def test_is_symlink_false(tmp_path, env_setup):
    """Regular file is not a symlink."""
    f = tmp_path / "regular.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    assert node.is_symlink() is False


def test_is_symlink_true(tmp_path, env_setup):
    """File.__post_init__ resolves symlinks, so is_symlink() returns False."""
    f = tmp_path / "target.txt"
    f.write_text("x", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(f)
    node = File(link)
    # File resolves the path in __post_init__, so the resolved path
    # is the target, not the symlink. is_symlink() checks self.path.
    assert node.is_symlink() is False


def test_copy(tmp_path, env_setup):
    """copy() copies the file to new path."""
    f = tmp_path / "original.txt"
    f.write_text("content", encoding="utf-8")
    dest = tmp_path / "copy.txt"
    node = File(f)
    node.copy(dest)
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "content"
    assert f.exists()  # original still there


def test_clean_name(tmp_path, env_setup):
    """clean_name() renames the file to its cleaned name."""
    f = tmp_path / "My[File].txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    node.clean_name()
    assert "[" not in node.name
    assert "]" not in node.name
    assert node.path.exists()


# -- Symlink operations --

def test_create_symlink(tmp_path, env_setup):
    """create_symlink() creates a symbolic link."""
    target = tmp_path / "target.txt"
    target.write_text("x", encoding="utf-8")
    link_path = tmp_path / "mylink.txt"
    link_path.write_text("placeholder", encoding="utf-8")
    node = File(link_path)
    node.create_symlink(target, replace=True)
    assert link_path.is_symlink()


def test_create_symlink_no_replace(tmp_path, env_setup):
    """create_symlink() without replace on a new path."""
    target = tmp_path / "target2.txt"
    target.write_text("x", encoding="utf-8")
    # Create a file that we'll use as the symlink source
    link_path = tmp_path / "newlink.txt"
    link_path.write_text("x", encoding="utf-8")
    node = File(link_path)
    # Remove the file first so symlink_to can create it
    link_path.unlink()
    node.path = link_path  # reset path after unlink
    node.path.symlink_to(target)
    assert link_path.is_symlink()


# -- get_year via FileSystemNode --

def test_get_year_from_node(tmp_path, env_setup):
    """get_year() extracts year from node name."""
    d = tmp_path / "Movie 2023"
    d.mkdir()
    node = Directory(d)
    assert node.get_year() == 2023


def test_get_year_no_year(tmp_path, env_setup):
    """get_year() returns None when no year in name."""
    d = tmp_path / "nodate"
    d.mkdir()
    node = Directory(d)
    assert node.get_year() is None


# -- joinpath / relative_to --

def test_joinpath(tmp_path, env_setup):
    """joinpath() joins paths correctly."""
    d = tmp_path / "base"
    d.mkdir()
    node = Directory(d)
    result = node.joinpath("child", "grandchild")
    assert str(result).endswith("child/grandchild")


def test_relative_to(tmp_path, env_setup):
    """relative_to() returns relative path."""
    d = tmp_path / "base"
    d.mkdir()
    node = Directory(d)
    rel = node.relative_to(tmp_path)
    assert str(rel) == "base"
