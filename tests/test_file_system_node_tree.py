"""Tests for FileSystemNodeTree."""
import json

import pytest
from pathlib import Path

from filemate.file import File
from filemate.directory import Directory
from filemate.file_system_node_tree import FileSystemNodeTree


# -- Build & basic attributes --

def test_build(tree_setup):
    """build() populates root_tree_node."""
    assert tree_setup.root_tree_node is not None
    assert tree_setup.root_tree_node.name == "tree_root"


def test_str(tree_setup):
    """__str__ includes root path."""
    s = str(tree_setup)
    assert "File System Node Tree" in s
    assert "tree_root" in s


def test_show(tree_setup, capsys):
    """show() prints tree without error."""
    tree_setup.show()
    captured = capsys.readouterr()
    assert "tree_root" in captured.out


def test_children(tree_setup):
    """children() returns child TreeNodes."""
    children = tree_setup.children()
    names = {c.name for c in children}
    assert "file_a.txt" in names
    assert "file_b.mp4" in names
    assert "subdir" in names


# -- Search methods --

def test_search_node_by_name_hit(tree_setup):
    """search_node_by_name finds existing node."""
    result = tree_setup.search_node_by_name("file_a.txt")
    assert result is not None
    assert result.name == "file_a.txt"


def test_search_node_by_name_nested(tree_setup):
    """search_node_by_name finds nested node."""
    result = tree_setup.search_node_by_name("nested.txt")
    assert result is not None
    assert result.name == "nested.txt"


def test_search_node_by_name_miss(tree_setup):
    """search_node_by_name returns None for missing node."""
    result = tree_setup.search_node_by_name("nonexistent.txt")
    assert result is None


def test_search_node_by_path_miss(tree_setup):
    """search_node_by_path returns None for path not in tree."""
    result = tree_setup.search_node_by_path(Path("/nonexistent/path"))
    assert result is None


# -- Add & Remove --

def test_add_node_parent_not_found(tree_setup, tmp_path, env_setup):
    """add_node raises ValueError when parent path not found."""
    f = tmp_path / "new_file.txt"
    f.write_text("new", encoding="utf-8")
    new_node = File(f)
    with pytest.raises(ValueError, match="not found"):
        tree_setup.add_node(Path("/bad/parent/path"), new_node)


def test_remove_node_not_found(tree_setup):
    """remove_node raises ValueError when path not found."""
    with pytest.raises(ValueError, match="not found"):
        tree_setup.remove_node(Path("/nonexistent/path"))


# -- Export & Import --

def test_tree_to_dict(tree_setup):
    """tree_to_dict returns dictionary representation."""
    d = tree_setup.tree_to_dict()
    assert isinstance(d, dict)
    assert len(d) > 0


def test_json(tree_setup):
    """json() returns valid JSON string."""
    j = tree_setup.json()
    parsed = json.loads(j)
    assert isinstance(parsed, dict)


def test_export_import_roundtrip(tree_setup, tmp_path):
    """export then import preserves tree structure."""
    export_path = str(tmp_path / "exported_tree.json")
    tree_setup.export(export_path)
    assert Path(export_path).exists()
    imported = FileSystemNodeTree.importer(export_path)
    # importer returns a TreeNode (via dict_to_tree), not a FileSystemNodeTree
    assert imported is not None
    assert imported.name == "tree_root"


def test_dict_to_tree_static():
    """dict_to_tree converts dictionary back to TreeNode."""
    data = {"/root": {"name": "root"}, "/root/child": {"name": "child"}}
    tree = FileSystemNodeTree.dict_to_tree(data)
    assert tree is not None
    assert tree.name == "root"


# -- Static utility --

def test_create_node_static(tmp_path, env_setup):
    """create_node creates a TreeNode from a FileSystemNode."""
    f = tmp_path / "static_test.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    tree_node = FileSystemNodeTree.create_node(node)
    assert tree_node.name == "static_test.txt"


def test_create_node_with_parent(tmp_path, env_setup):
    """create_node attaches child to parent TreeNode."""
    from bigtree import Node as TreeNode

    parent_tn = TreeNode("parent")
    f = tmp_path / "child.txt"
    f.write_text("x", encoding="utf-8")
    child_node = File(f)
    child_tn = FileSystemNodeTree.create_node(child_node, parent=parent_tn)
    assert child_tn.parent is parent_tn
    assert child_tn in parent_tn.children


# -- Validation --

def test_post_init_non_directory_raises(tmp_path, env_setup, mock_redis):
    """ValueError when root_node is not a Directory."""
    f = tmp_path / "not_dir.txt"
    f.write_text("x", encoding="utf-8")
    file_node = File(f)
    with pytest.raises(ValueError, match="not a directory"):
        FileSystemNodeTree(file_node)


# -- Save / Restore / Check --

def test_check_saved_tree_not_exists():
    """check_saved_tree returns False when no saved tree."""
    assert FileSystemNodeTree.check_saved_tree("nonexistent_tree_name") is False


def test_save_and_check_and_restore(tree_setup, tmp_path, monkeypatch):
    """save() writes JSON file, check returns True, restore() reads it back."""
    monkeypatch.chdir(tmp_path)
    tree_setup.save()
    assert FileSystemNodeTree.check_saved_tree("tree_root") is True
    restored = FileSystemNodeTree.restore("tree_root")
    # restore returns a TreeNode (via importer -> dict_to_tree)
    assert restored is not None
    assert restored.name == "tree_root"


def test_save_overwrites_existing(tree_setup, tmp_path, monkeypatch):
    """save() overwrites an existing saved tree."""
    monkeypatch.chdir(tmp_path)
    tree_setup.save()
    # Save again; should overwrite without error
    tree_setup.save()
    assert FileSystemNodeTree.check_saved_tree("tree_root") is True


def test_check_saved_tree_max_age(tree_setup, tmp_path, monkeypatch):
    """check_saved_tree with max_age respects file age."""
    monkeypatch.chdir(tmp_path)
    tree_setup.save()
    # File was just created, so max_age=3600 should return True
    assert FileSystemNodeTree.check_saved_tree("tree_root", max_age=3600) is True
    # max_age=0 should return False (file is already >= 0 seconds old)
    assert FileSystemNodeTree.check_saved_tree("tree_root", max_age=0) is False


def test_check_saved_tree_max_age_no_file():
    """check_saved_tree with max_age returns False when file doesn't exist."""
    assert FileSystemNodeTree.check_saved_tree("ghost", max_age=3600) is False


def test_restore_not_saved():
    """restore raises FileNotFoundError when no saved tree."""
    with pytest.raises(FileNotFoundError, match="No saved tree"):
        FileSystemNodeTree.restore("nonexistent_tree_name")
