"""Packer module for transferring nodes between file system trees."""

from dataclasses import dataclass, field
from enum import Enum

from pydevmate import LogIt

from filemate.directory import Directory
from filemate.exceptions import TransferError
from filemate.file_system_node import FileSystemNode
from filemate.file_system_node_tree import FileSystemNodeTree


class ConflictPolicy(Enum):
    """Policy for handling conflicts when a node already exists at destination.

    Attributes:
        SKIP: Leave the existing destination node untouched.
        REPLACE: Remove the destination node and add the source node.
        MERGE: Recursively merge directory contents; replace files.
    """

    SKIP = "skip"
    REPLACE = "replace"
    MERGE = "merge"


@dataclass
class Packer:
    """Transfer nodes between two FileSystemNodeTree instances.

    Attributes:
        source: The source tree.
        destination: The destination tree.
        policy: Conflict resolution policy.
        dry_run: If True, log actions without performing them.
        verbose: If True, emit extra log output.
        logger: Logger instance.
    """

    source: FileSystemNodeTree = field(init=True, default=None)
    destination: FileSystemNodeTree = field(init=True, default=None)
    policy: ConflictPolicy = field(init=True, default=ConflictPolicy.SKIP)
    dry_run: bool = field(init=True, default=False)
    verbose: bool = field(init=True, default=False)
    logger: LogIt = field(init=True, default_factory=LogIt)

    def transfer(self, node_name: str) -> str:
        """Transfer a single top-level node from source to destination.

        Args:
            node_name: Name of the node to transfer.

        Returns:
            The name of the transferred node.

        Raises:
            TransferError: If the node is not found in the source tree.
        """
        src_node = self.source.search_node_by_name(node_name)
        if src_node is None:
            raise TransferError(f"Node '{node_name}' not found in source tree.")

        dst_node = self.destination.search_node_by_name(node_name)

        if dst_node is not None:
            self._resolve_conflict(src_node, dst_node)
        else:
            self._add_node(src_node)

        return node_name

    def transfer_all(self) -> list[str]:
        """Transfer all top-level children from source to destination.

        Returns:
            List of transferred node names.
        """
        transferred = []
        for child in self.source.children():
            name = child.name
            try:
                self.transfer(name)
                transferred.append(name)
            except TransferError as e:
                self.logger.warning(str(e))
        return transferred

    def _resolve_conflict(self, src_node, dst_node) -> None:
        """Handle a conflict where the node exists in both trees.

        Args:
            src_node: The source tree node.
            dst_node: The destination tree node.
        """
        if self.policy == ConflictPolicy.SKIP:
            if self.verbose:
                self.logger.info(f"Skipping existing node: {src_node.name}")
            return

        if self.policy == ConflictPolicy.REPLACE:
            if not self.dry_run:
                dst_node.parent = None  # detach existing
                self._add_node(src_node)
            else:
                self.logger.info(f"Would replace: {src_node.name}")
            return

        if self.policy == ConflictPolicy.MERGE:
            if not self.dry_run:
                # For merge, add children of source that don't exist in destination
                for child in getattr(src_node, "children", []) or []:
                    existing = self.destination.search_node_by_name(child.name)
                    if existing is None:
                        self._add_child_node(child, dst_node)
                    else:
                        # Recursively resolve
                        self._resolve_conflict(child, existing)
            else:
                self.logger.info(f"Would merge: {src_node.name}")

    def _add_node(self, src_node) -> None:
        """Add a source node under the destination root.

        Args:
            src_node: The source tree node to add.
        """
        if not self.dry_run:
            from bigtree import Node as TreeNode

            TreeNode(src_node.name, parent=self.destination.root_tree_node)

    def _add_child_node(self, src_node, dst_parent) -> None:
        """Add a source node as a child of a destination node.

        Args:
            src_node: The source tree node to add.
            dst_parent: The destination parent node.
        """
        if not self.dry_run:
            from bigtree import Node as TreeNode

            TreeNode(src_node.name, parent=dst_parent)

    def __str__(self) -> str:
        """Return a string summary of the packer."""
        src = self.source.root_node.path if self.source else "None"
        dst = self.destination.root_node.path if self.destination else "None"
        return f"Packer: Source={src}, Destination={dst}"

    def __repr__(self) -> str:
        """Return a string summary of the packer."""
        return self.__str__()

    def __bool__(self) -> bool:
        """Return True if both source and destination are set."""
        return self.source is not None and self.destination is not None

    def __call__(
        self,
        node_name: str,
    ) -> str:
        """Shortcut for transfer().

        Args:
            node_name: Name of the node to transfer.

        Returns:
            The name of the transferred node.
        """
        return self.transfer(node_name)
