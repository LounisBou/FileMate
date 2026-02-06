"""Hierarchical tree representation of a filesystem structure."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from bigtree import Node as TreeNode
from bigtree import dict_to_tree, print_tree, tree_to_dict
from pydevmate import CacheIt, LogIt, SaveIt, TimeIt
from termcolor import colored

from filemate.directory import Directory
from filemate.file_system_node import FileSystemNode


@dataclass
class FileSystemNodeTree:
    """A hierarchical tree of filesystem nodes backed by bigtree.

    Attributes:
        nodetree_folder_name: Default folder name for persisted trees.
        redis_config: Default Redis connection parameters.
        root_node: The root Directory node.
        verbose: If True, emit extra log output.
        root_tree_node: The root bigtree TreeNode.
        logger: Logger instance.
        saveit: SaveIt instance for persistence (may be None if Redis unavailable).
    """

    nodetree_folder_name: ClassVar[str] = "__nodetree__"
    redis_config: ClassVar[dict] = {"host": "localhost", "port": 6379, "db": 0}

    root_node: FileSystemNode = field(init=True)
    verbose: bool = field(init=True, default=False)
    root_tree_node: TreeNode = field(init=False, default=None)
    logger: LogIt = field(init=True, default_factory=LogIt)
    saveit: SaveIt = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Validate root node and initialize SaveIt.

        Raises:
            ValueError: If the root node is not a Directory.
        """
        if not self.root_node.is_instance(Directory):
            raise ValueError(f"The root node {self.root_node} is not a directory.")
        try:
            self.saveit = SaveIt(
                backend="redis",
                redis_config=FileSystemNodeTree.redis_config,
            )
        except Exception:
            self.saveit = None

    # -- Build --

    @TimeIt
    def __build_tree(self) -> None:
        """Build the complete tree starting from root_node."""
        self.root_tree_node = FileSystemNodeTree.create_node(self.root_node)
        self.__build_tree_recursive(self.root_node, self.root_tree_node)

    @CacheIt(max_duration=3600, backend="redis", redis_config=redis_config)
    def __build_tree_recursive(
        self, node: Directory, tree_node: TreeNode
    ) -> None:
        """Recursively build tree nodes for all children.

        Args:
            node: The filesystem Directory to recurse into.
            tree_node: The parent bigtree TreeNode.
        """
        for child_node in node.iter(recursive=False, hidden=False):
            try:
                child_tree_node = FileSystemNodeTree.create_node(
                    child_node, parent=tree_node
                )
                if child_node.is_instance(Directory):
                    self.__build_tree_recursive(child_node, child_tree_node)
            except PermissionError as e:
                self.logger.info(
                    colored(
                        f"Skipping node {child_node.path.name} due to error: {e}",
                        "yellow",
                    )
                )

    def __str__(self) -> str:
        """Return a string summary."""
        return f"File System Node Tree: {self.root_node.path}"

    # -- Public: Build --

    def build(self) -> None:
        """Build the tree of filesystem nodes."""
        self.__build_tree()

    # -- Public: Add & Remove --

    def add_node(self, parent_path: Path, child_node: FileSystemNode) -> None:
        """Add a new node to the tree under *parent_path*.

        Args:
            parent_path: Path of the parent node in the tree.
            child_node: The filesystem node to add.

        Raises:
            ValueError: If *parent_path* is not found in the tree.
        """
        parent_tree_node = self.search_node_by_path(parent_path)
        if parent_tree_node is None:
            raise ValueError(f"Parent path {parent_path} not found in the tree.")
        FileSystemNodeTree.create_node(child_node, parent=parent_tree_node)

    def remove_node(self, path: Path) -> None:
        """Remove a node from the tree by path.

        Args:
            path: Path of the node to remove.

        Raises:
            ValueError: If *path* is not found in the tree.
        """
        node_to_remove = self.search_node_by_path(path)
        if node_to_remove is None:
            raise ValueError(f"Path {path} not found in the tree.")
        node_to_remove.parent = None

    # -- Public: Display --

    def show(self) -> None:
        """Print the tree to stdout."""
        print_tree(self.root_tree_node)

    # -- Public: Export & Import --

    def tree_to_dict(self) -> dict:
        """Convert the tree to a dictionary.

        Returns:
            Dictionary representation of the tree.
        """
        return tree_to_dict(self.root_tree_node)

    @staticmethod
    def dict_to_tree(data: dict) -> TreeNode:
        """Convert a dictionary back to a TreeNode.

        Args:
            data: Dictionary representation.

        Returns:
            The root TreeNode.
        """
        return dict_to_tree(data)

    def json(self, indent: int = 4) -> str:
        """Serialize the tree as a JSON string.

        Args:
            indent: Number of spaces for indentation.

        Returns:
            JSON string.
        """
        return json.dumps(self.tree_to_dict(), indent=indent)

    def export(self, file_path: str, indent: int = 4) -> None:
        """Export the tree to a JSON file.

        Args:
            file_path: Path to save the file.
            indent: Number of spaces for indentation.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.json(indent=indent))

    @staticmethod
    def importer(file_path: str) -> "FileSystemNodeTree":
        """Import a tree from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            A TreeNode reconstructed from the file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            tree_data = json.load(f)
        return FileSystemNodeTree.dict_to_tree(tree_data)

    # -- Public: Search --

    def search_node_by_name(self, name: str) -> TreeNode | None:
        """Find a node in the tree by name.

        Args:
            name: The node name to search for.

        Returns:
            The matching TreeNode, or None.
        """

        def _find_by_name(node, target):
            if node.name == target:
                return node
            for child in getattr(node, "children", []):
                result = _find_by_name(child, target)
                if result is not None:
                    return result
            return None

        return _find_by_name(self.root_tree_node, name)

    def search_node_by_path(self, path: Path) -> TreeNode | None:
        """Find a node in the tree by absolute or relative path.

        Computes the path relative to the tree root before searching,
        so absolute paths work correctly.

        Args:
            path: Path to search for.

        Returns:
            The matching TreeNode, or None.
        """
        resolved = Path(path).resolve()
        root_path = self.root_node.path

        # If the path is the root itself, return root
        if resolved == root_path:
            return self.root_tree_node

        # Try to compute relative path from the root
        try:
            relative = resolved.relative_to(root_path)
        except ValueError:
            return None  # path is outside the tree

        current_node = self.root_tree_node
        for part in relative.parts:
            current_node = next(
                (child for child in current_node.children if child.name == part),
                None,
            )
            if current_node is None:
                return None

        return current_node

    # -- Public: Save / Restore --

    @TimeIt
    def save(self) -> None:
        """Save the tree to a JSON file in the nodetree folder."""
        nodetree_folder = Path(FileSystemNodeTree.nodetree_folder_name)
        if not nodetree_folder.exists():
            nodetree_folder.mkdir()
        if FileSystemNodeTree.check_saved_tree(self.root_node.name):
            (nodetree_folder / f"{self.root_node.name}.json").unlink()
        self.export(
            f"{FileSystemNodeTree.nodetree_folder_name}/{self.root_node.name}.json"
        )

    @staticmethod
    @TimeIt
    def restore(node_name: str) -> "FileSystemNodeTree":
        """Restore a tree from a previously saved JSON file.

        Args:
            node_name: Name of the root node.

        Returns:
            The restored TreeNode.

        Raises:
            FileNotFoundError: If no saved tree is found.
        """
        if not FileSystemNodeTree.check_saved_tree(node_name):
            raise FileNotFoundError("No saved tree found.")
        return FileSystemNodeTree.importer(
            f"{FileSystemNodeTree.nodetree_folder_name}/{node_name}.json"
        )

    @staticmethod
    def check_saved_tree(node_name: str, max_age: int | None = None) -> bool:
        """Check if a saved tree file exists (and optionally is recent enough).

        Args:
            node_name: Name of the root node.
            max_age: Maximum age in seconds. None to ignore.

        Returns:
            True if a valid saved tree exists.
        """
        if max_age is not None:
            nodetree_path = Path(
                f"{FileSystemNodeTree.nodetree_folder_name}/{node_name}.json"
            )
            if nodetree_path.exists():
                return (time.time() - nodetree_path.stat().st_mtime) < max_age
            return False
        return Path(
            f"{FileSystemNodeTree.nodetree_folder_name}/{node_name}.json"
        ).exists()

    # -- Static utility --

    @staticmethod
    def create_node(
        node: FileSystemNode, parent: TreeNode = None
    ) -> TreeNode:
        """Create a bigtree TreeNode from a FileSystemNode.

        Args:
            node: The filesystem node.
            parent: Optional parent TreeNode.

        Returns:
            The created TreeNode.
        """
        return TreeNode(
            node.path.name,
            parent=parent,
            size=node.get_size(),
            type=node.get_type(),
        )

    def children(self) -> list[TreeNode]:
        """Return the children of the root tree node.

        Returns:
            List of child TreeNodes.
        """
        return self.root_tree_node.children
