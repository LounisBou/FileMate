#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""FileMate CLI entry point."""

from pydevmate import LogIt

from commandlinehelper import check_args, parse_args, set_default_args_values
from filemate.config import AppSettings
from filemate.file_system_node import FileSystemNode
from filemate.file_system_node_factory import FileSystemNodeFactory
from filemate.file_system_node_tree import FileSystemNodeTree
from filemate.node_name_cleaner import NodeNameCleaner
from filemate.sorter import Sorter


def main() -> None:
    """Entry point for the FileMate application."""
    # Parse and validate arguments
    args = parse_args()
    args = check_args(args)
    args = set_default_args_values(args)

    # Load settings and configure shared cleaner
    settings = AppSettings()
    cleaner = NodeNameCleaner(settings)
    FileSystemNode.set_name_cleaner(cleaner)

    logger = LogIt(console=True, format="%(message)s")

    # Create node from validated path
    node = FileSystemNodeFactory.create_node(args.path)

    # Check if tree is requested
    if args.tree:
        if FileSystemNodeTree.check_saved_tree(node.name):
            file_system_node_tree = FileSystemNodeTree.restore(node.name)
        else:
            file_system_node_tree = FileSystemNodeTree(
                node, verbose=args.verbose, logger=logger
            )
            file_system_node_tree.build()
        if args.show_tree:
            file_system_node_tree.show()

    # Check if sort is requested
    if args.sort:
        file_sorter = Sorter(
            node,
            verbose=args.verbose,
            dry_run=args.dry_run,
            settings=settings,
            logger=logger,
        )
        file_sorter.process(delete_remaining_element=args.clean)


if __name__ == "__main__":
    main()