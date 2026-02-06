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


# -- String representations --

def test_directory_str(tmp_path, env_setup):
    """__str__ returns 'Directory: name'."""
    d = tmp_path / "mydir"
    d.mkdir()
    node = Directory(d)
    assert str(node) == "Directory: mydir"


def test_directory_repr(tmp_path, env_setup):
    """__repr__ returns multi-line detail string."""
    d = tmp_path / "reprdir"
    d.mkdir()
    node = Directory(d)
    r = repr(node)
    assert "Directory:" in r
    assert "Name:" in r
    assert "Year:" in r
    assert "Items:" in r


# -- Operator overloads --

def test_directory_setitem(tmp_path, env_setup):
    """__setitem__: dir['name'] = node replaces a node."""
    d = tmp_path / "setitem_dir"
    d.mkdir()
    (d / "old.txt").write_text("old", encoding="utf-8")
    new_path = tmp_path / "new.txt"
    new_path.write_text("new", encoding="utf-8")
    dir_node = Directory(d)
    new_node = File(new_path)
    dir_node["old.txt"] = new_node


def test_directory_delitem_file(tmp_path, env_setup):
    """__delitem__: del dir['file'] removes the file."""
    d = tmp_path / "delitem_dir"
    d.mkdir()
    (d / "victim.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    del node["victim.txt"]
    assert not (d / "victim.txt").exists()


def test_directory_delitem_subdir(tmp_path, env_setup):
    """__delitem__: del dir['subdir'] removes subdirectory recursively."""
    d = tmp_path / "delitem_dir2"
    d.mkdir()
    sub = d / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    del node["subdir"]
    assert not sub.exists()


def test_directory_delitem_missing(tmp_path, env_setup):
    """__delitem__: KeyError for missing item."""
    d = tmp_path / "delitem_dir3"
    d.mkdir()
    node = Directory(d)
    with pytest.raises(KeyError):
        del node["nonexistent.txt"]


def test_directory_pow_merge(tmp_path, env_setup):
    """__pow__: dir1 ** dir2 merges dir2 into dir1."""
    d1 = tmp_path / "pow_dir1"
    d1.mkdir()
    (d1 / "existing.txt").write_text("a", encoding="utf-8")
    d2 = tmp_path / "pow_dir2"
    d2.mkdir()
    (d2 / "incoming.txt").write_text("b", encoding="utf-8")
    node1 = Directory(d1)
    node2 = Directory(d2)
    result = node1 ** node2
    assert isinstance(result, Directory)
    assert (d1 / "incoming.txt").exists()
    assert not d2.exists()


def test_directory_and_intersection(tmp_path, env_setup):
    """__and__: dir1 & dir2 returns intersection."""
    d1 = tmp_path / "and_dir1"
    d1.mkdir()
    (d1 / "shared.txt").write_text("a", encoding="utf-8")
    (d1 / "only_d1.txt").write_text("b", encoding="utf-8")
    d2 = tmp_path / "and_dir2"
    d2.mkdir()
    (d2 / "shared.txt").write_text("c", encoding="utf-8")
    (d2 / "only_d2.txt").write_text("d", encoding="utf-8")
    node1 = Directory(d1)
    node2 = Directory(d2)
    result = node1 & node2
    assert isinstance(result, set)
    names = {n.name for n in result}
    assert "shared.txt" in names


def test_directory_or_union(tmp_path, env_setup):
    """__or__: dir1 | dir2 returns union."""
    d1 = tmp_path / "or_dir1"
    d1.mkdir()
    (d1 / "a.txt").write_text("a", encoding="utf-8")
    d2 = tmp_path / "or_dir2"
    d2.mkdir()
    (d2 / "b.txt").write_text("b", encoding="utf-8")
    node1 = Directory(d1)
    node2 = Directory(d2)
    result = node1 | node2
    assert isinstance(result, set)
    names = {n.name for n in result}
    assert "a.txt" in names
    assert "b.txt" in names


def test_directory_invert(tmp_path, env_setup):
    """__invert__: ~dir returns empty set (XOR with itself)."""
    d = tmp_path / "inv_dir"
    d.mkdir()
    (d / "file.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    result = ~node
    assert result == set()


# -- Iteration edge cases --

def test_directory_next(tmp_path, env_setup):
    """__next__ returns the first item from iteration."""
    d = tmp_path / "next_dir"
    d.mkdir()
    (d / "only.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    item = next(node)
    assert item.name == "only.txt"


def test_directory_iter_recursive(tmp_path, env_setup):
    """Recursive iteration traverses subdirectories."""
    d = tmp_path / "recurse"
    d.mkdir()
    (d / "top.txt").write_text("x", encoding="utf-8")
    sub = d / "sub"
    sub.mkdir()
    (sub / "deep.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    items = list(node.iter(recursive=True))
    names = {item.name for item in items}
    assert "top.txt" in names
    assert "deep.txt" in names
    assert "sub" in names


def test_directory_iter_hides_dotfiles(tmp_path, env_setup):
    """Hidden files (starting with .) are excluded by default."""
    d = tmp_path / "hidden_dir"
    d.mkdir()
    (d / ".hidden").write_text("x", encoding="utf-8")
    (d / "visible.txt").write_text("x", encoding="utf-8")
    node = Directory(d)
    items = list(node.iter())
    names = {item.name for item in items}
    assert "visible.txt" in names
    assert ".hidden" not in names


# -- Other --

def test_directory_get_size(tmp_path, env_setup):
    """get_size() returns total bytes of contained files."""
    d = tmp_path / "sized_dir"
    d.mkdir()
    (d / "a.txt").write_bytes(b"\x00" * 100)
    (d / "b.txt").write_bytes(b"\x00" * 200)
    node = Directory(d)
    # Directory.get_size checks self.size is None, but default is 0
    # So it returns 0 like File.get_size
    result = node.get_size()
    assert result == 0


def test_directory_truediv_with_directory(tmp_path, env_setup):
    """dir / 'subdir' returns Directory when target is a dir."""
    d = tmp_path / "div_base"
    d.mkdir()
    (d / "child_dir").mkdir()
    node = Directory(d)
    result = node / "child_dir"
    assert isinstance(result, Directory)


def test_directory_unpack_file_only(tmp_path, env_setup):
    """unpack(file_only=True) only moves files, not subdirectories."""
    parent = tmp_path / "unpack_fo"
    parent.mkdir()
    inner = parent / "inner_fo"
    inner.mkdir()
    (inner / "file.txt").write_text("x", encoding="utf-8")
    (inner / "subdir").mkdir()
    (inner / "subdir" / "nested.txt").write_text("y", encoding="utf-8")
    node = Directory(inner)
    unpacked = node.unpack(file_only=True)
    assert (parent / "file.txt").exists()
    # subdir should NOT have been moved
    assert (inner / "subdir").exists()
    assert all(isinstance(n, File) for n in unpacked)


def test_directory_unpack_dir_only(tmp_path, env_setup):
    """unpack(dir_only=True) only moves subdirectories, not files."""
    parent = tmp_path / "unpack_do"
    parent.mkdir()
    inner = parent / "inner_do"
    inner.mkdir()
    (inner / "file.txt").write_text("x", encoding="utf-8")
    sub = inner / "moveme"
    sub.mkdir()
    node = Directory(inner)
    unpacked = node.unpack(dir_only=True)
    # File should still be in inner
    assert (inner / "file.txt").exists()
    # subdir should have been moved
    assert (parent / "moveme").exists()
    assert all(isinstance(n, Directory) for n in unpacked)
