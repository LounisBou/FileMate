"""Tests for the Packer class."""

import pytest
from unittest.mock import MagicMock

from filemate.directory import Directory
from filemate.exceptions import TransferError
from filemate.file_system_node_tree import FileSystemNodeTree
from filemate.packer import ConflictPolicy, Packer


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


# -- transfer() --


def test_transfer_skip(tmp_path, env_setup, mock_redis):
    """With SKIP policy, existing destination node is left untouched."""
    src = _make_tree(tmp_path, "src", [("a.txt", "src_a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst, policy=ConflictPolicy.SKIP)
    result = packer.transfer("a.txt")
    assert result == "a.txt"
    # Destination tree should still have the original node
    assert dst.search_node_by_name("a.txt") is not None


def test_transfer_replace(tmp_path, env_setup, mock_redis):
    """With REPLACE policy, existing destination node is replaced."""
    src = _make_tree(tmp_path, "src", [("a.txt", "src_a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst, policy=ConflictPolicy.REPLACE)
    result = packer.transfer("a.txt")
    assert result == "a.txt"
    # A node named a.txt should exist in destination (the replacement)
    assert dst.search_node_by_name("a.txt") is not None


def test_transfer_merge(tmp_path, env_setup, mock_redis):
    """With MERGE policy, source children are merged into destination."""
    # Source has a subdir with a file
    src_root = tmp_path / "src"
    src_root.mkdir()
    src_sub = src_root / "sub"
    src_sub.mkdir()
    (src_sub / "new.txt").write_text("new", encoding="utf-8")
    src_tree = FileSystemNodeTree(Directory(src_root))
    src_tree.build()

    # Destination has the same subdir but different file
    dst_root = tmp_path / "dst"
    dst_root.mkdir()
    dst_sub = dst_root / "sub"
    dst_sub.mkdir()
    (dst_sub / "old.txt").write_text("old", encoding="utf-8")
    dst_tree = FileSystemNodeTree(Directory(dst_root))
    dst_tree.build()

    packer = Packer(source=src_tree, destination=dst_tree, policy=ConflictPolicy.MERGE)
    result = packer.transfer("sub")
    assert result == "sub"
    # new.txt should now be in destination under sub
    assert dst_tree.search_node_by_name("new.txt") is not None
    # old.txt should still be there
    assert dst_tree.search_node_by_name("old.txt") is not None


def test_transfer_new_node(tmp_path, env_setup, mock_redis):
    """Node not in destination is added."""
    src = _make_tree(tmp_path, "src", [("unique.txt", "data")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("other.txt", "other")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    result = packer.transfer("unique.txt")
    assert result == "unique.txt"
    assert dst.search_node_by_name("unique.txt") is not None


def test_transfer_not_found(tmp_path, env_setup, mock_redis):
    """TransferError for node not in source."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("b.txt", "b")], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    with pytest.raises(TransferError, match="not found"):
        packer.transfer("nonexistent.txt")


def test_transfer_all(tmp_path, env_setup, mock_redis):
    """transfer_all transfers all top-level nodes."""
    src = _make_tree(
        tmp_path, "src", [("a.txt", "a"), ("b.txt", "b")], env_setup, mock_redis
    )
    dst = _make_tree(tmp_path, "dst", [], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    result = packer.transfer_all()
    assert "a.txt" in result
    assert "b.txt" in result


def test_dry_run(tmp_path, env_setup, mock_redis):
    """Dry run does not modify destination tree."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [("a.txt", "dst_a")], env_setup, mock_redis)
    packer = Packer(
        source=src,
        destination=dst,
        policy=ConflictPolicy.REPLACE,
        dry_run=True,
    )
    packer.transfer("a.txt")
    # In dry run, destination should still have only its original children
    children = dst.children()
    assert len(children) == 1


# -- __call__ --


def test_packer_call(tmp_path, env_setup, mock_redis):
    """__call__ delegates to transfer."""
    src = _make_tree(tmp_path, "src", [("a.txt", "a")], env_setup, mock_redis)
    dst = _make_tree(tmp_path, "dst", [], env_setup, mock_redis)
    packer = Packer(source=src, destination=dst)
    result = packer("a.txt")
    assert result == "a.txt"
