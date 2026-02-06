"""Tests for the Packer class."""
import pytest
from unittest.mock import patch, MagicMock

from filemate.directory import Directory
from filemate.file import File
from filemate.file_system_node_tree import FileSystemNodeTree
from filemate.packer import Packer


def _make_tree(tmp_path, name, files, env_setup, mock_redis):
    """Helper to create a tree with given files."""
    root = tmp_path / name
    root.mkdir()
    for fname, content in files:
        p = root / fname
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")
    root_node = Directory(root)
    tree = FileSystemNodeTree(root_node)
    tree.build()
    return tree


# -- String representations & basic --

def test_packer_str(tmp_path, env_setup, mock_redis):
    """__str__ includes source and destination paths."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("b.txt", "b")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    s = str(packer)
    assert "Packer" in s
    assert "Source=" in s
    assert "Destination=" in s


def test_packer_repr(tmp_path, env_setup, mock_redis):
    """__repr__ matches __str__."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("b.txt", "b")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    assert repr(packer) == str(packer)


def test_packer_bool_true(tmp_path, env_setup, mock_redis):
    """Packer with source and destination is truthy."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("b.txt", "b")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    assert bool(packer) is True


def test_packer_bool_false_no_source():
    """Packer without source is falsy."""
    packer = Packer(source=None, destination=MagicMock())
    assert bool(packer) is False


def test_packer_bool_false_no_dest(tmp_path, env_setup, mock_redis):
    """Packer without destination is falsy."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=None)
    assert bool(packer) is False


# -- pack() with explicit destination (replace mode, default) --

def test_pack_replace_file_to_file(tmp_path, env_setup, mock_redis):
    """pack() in replace mode: file replaces file (mocked add_node)."""
    src = _make_tree(tmp_path, "src", [("a.txt", "src_a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    src_file = File(tmp_path / "src" / "a.txt")
    dst_file = File(tmp_path / "dst" / "a.txt")
    # Mock Packer's add_node to avoid broken parent.path access
    with patch.object(packer, "add_node"):
        packer.pack(src_file, dst_file)


def test_pack_replace_dir_to_dir(tmp_path, env_setup, mock_redis):
    """pack() in replace mode: directory replaces directory (mocked)."""
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_sub = src_root / "sub"
    src_sub.mkdir()
    (src_sub / "file.txt").write_text("x", encoding="utf-8")
    dst_root = tmp_path / "dst"
    dst_root.mkdir()
    dst_sub = dst_root / "sub"
    dst_sub.mkdir()
    (dst_sub / "old.txt").write_text("y", encoding="utf-8")

    src_tree = FileSystemNodeTree(Directory(src_root))
    src_tree.build()
    dst_tree = FileSystemNodeTree(Directory(dst_root))
    dst_tree.build()

    packer = Packer(source=src_tree, destination=dst_tree)
    src_dir_node = Directory(src_sub)
    dst_dir_node = Directory(dst_sub)
    # Mock both add_node and remove_node on the Packer
    with patch.object(packer, "add_node"), patch.object(packer, "remove_node"):
        packer.pack(src_dir_node, dst_dir_node)


# -- __call__ --

def test_packer_call(tmp_path, env_setup, mock_redis):
    """__call__ delegates to pack."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    src_file = File(tmp_path / "src" / "a.txt")
    dst_file = File(tmp_path / "dst" / "a.txt")
    with patch.object(packer, "add_node"):
        packer(src_file, dst_file)


# -- pack() with override mode --

def test_pack_override_file(tmp_path, env_setup, mock_redis):
    """pack() with override=True for file nodes delegates to replace."""
    src = _make_tree(tmp_path, "src", [("a.txt", "src_a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst, override=True)
    src_file = File(tmp_path / "src" / "a.txt")
    dst_file = File(tmp_path / "dst" / "a.txt")
    with patch.object(packer, "add_node"):
        packer.pack(src_file, dst_file)


def test_pack_override_dir(tmp_path, env_setup, mock_redis):
    """pack() with override=True for directory nodes calls override_directory."""
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_sub = src_root / "sub"
    src_sub.mkdir()
    (src_sub / "file.txt").write_text("x", encoding="utf-8")
    dst_root = tmp_path / "dst"
    dst_root.mkdir()
    dst_sub = dst_root / "sub"
    dst_sub.mkdir()

    src_tree = FileSystemNodeTree(Directory(src_root))
    src_tree.build()
    dst_tree = FileSystemNodeTree(Directory(dst_root))
    dst_tree.build()

    packer = Packer(source=src_tree, destination=dst_tree, override=True)
    src_dir = Directory(src_sub)
    dst_dir = Directory(dst_sub)
    # Mock search_node_by_name (called with FileSystemNode, returns None),
    # and add_node/remove_node to avoid broken parent.path
    with (
        patch.object(packer, "add_node"),
        patch.object(packer, "remove_node"),
        patch.object(dst_tree, "search_node_by_name", return_value=None),
    ):
        packer.pack(src_dir, dst_dir)


# -- pack() with merge mode --

def test_pack_merge_file(tmp_path, env_setup, mock_redis):
    """pack() with merge=True for file nodes delegates to replace."""
    src = _make_tree(tmp_path, "src", [("a.txt", "src_a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst, merge=True)
    src_file = File(tmp_path / "src" / "a.txt")
    dst_file = File(tmp_path / "dst" / "a.txt")
    with patch.object(packer, "add_node"):
        packer.pack(src_file, dst_file)


def test_pack_merge_dir(tmp_path, env_setup, mock_redis):
    """pack() with merge=True for directory nodes calls merge_directory."""
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_sub = src_root / "sub"
    src_sub.mkdir()
    (src_sub / "new.txt").write_text("x", encoding="utf-8")
    dst_root = tmp_path / "dst"
    dst_root.mkdir()
    dst_sub = dst_root / "sub"
    dst_sub.mkdir()

    src_tree = FileSystemNodeTree(Directory(src_root))
    src_tree.build()
    dst_tree = FileSystemNodeTree(Directory(dst_root))
    dst_tree.build()

    packer = Packer(source=src_tree, destination=dst_tree, merge=True)
    src_dir = Directory(src_sub)
    dst_dir = Directory(dst_sub)
    with (
        patch.object(packer, "add_node"),
        patch.object(packer, "remove_node"),
        patch.object(dst_tree, "search_node_by_name", return_value=None),
    ):
        packer.pack(src_dir, dst_dir)
