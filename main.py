#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from pymate import LogIt

from commandlinehelper import parse_args, check_args, set_default_args_values
from filemate.file_system_node_factory import FileSystemNodeFactory
from filemate.file_system_node_tree import FileSystemNodeTree
from filemate.sorter import Sorter


def main() -> None:
    """
    Entry point for the FileMate application.
    """

    # Parse and validate arguments
    args = parse_args()
    args = check_args(args)
    args = set_default_args_values(args)
    
    # Get the logger
    logger = LogIt(console=True, format='%(message)s')

    # Create node from validated path
    node = FileSystemNodeFactory.create_node(args.path)
    
    # Check if tree is requested
    if args.tree:
        # Check if the node tree saved file exists
        if FileSystemNodeTree.check_saved_tree(node.name):
            # Load the tree
            file_system_node_tree = FileSystemNodeTree.restore(node.name)
        else:
            # Create the tree
            file_system_node_tree = FileSystemNodeTree(
                node,
                verbose=args.verbose,
                logger=logger
            )
            # Build the tree
            file_system_node_tree.build()
            # Save the tree
            #file_system_node_tree.save()
        # Print the node tree
        if args.show_tree:
            file_system_node_tree.show()
        
    # Check if sort is requested
    if args.sort:
        # Sort nodes
        file_sorter = Sorter(
            node,
            verbose=args.verbose,
            dry_run=args.dry_run,
            logger=logger,
        )
        file_sorter.process(delete_remaining_element=args.clean)

  
# Check if the script is being run directly
if __name__ == "__main__":
    # Run the main function
    main()