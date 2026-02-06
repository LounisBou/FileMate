"""FileMate - A NAS FileSystem management tool."""

from ._about import __version__
from .config import AppSettings
from .directory import Directory
from .exceptions import ConfigError, FileMateError, NodeNotFoundError, SortingError, TransferError
from .file import File
from .file_system_node import FileSystemNode
from .file_system_node_factory import FileSystemNodeFactory
from .file_system_node_tree import FileSystemNodeTree
from .file_type import FileType
from .file_type_extensions import FileTypeExtensions
from .node_name_cleaner import NodeNameCleaner
from .packer import ConflictPolicy, Packer
from .sorter import Sorter
from .sorting_strategies import DefaultStrategy, MovieStrategy, SortingStrategy, TVShowStrategy

__all__ = [
    "__version__",
    "AppSettings",
    "ConfigError",
    "ConflictPolicy",
    "DefaultStrategy",
    "Directory",
    "File",
    "FileMateError",
    "FileSystemNode",
    "FileSystemNodeFactory",
    "FileSystemNodeTree",
    "FileType",
    "FileTypeExtensions",
    "MovieStrategy",
    "NodeNameCleaner",
    "NodeNotFoundError",
    "Packer",
    "Sorter",
    "SortingError",
    "SortingStrategy",
    "TransferError",
    "TVShowStrategy",
]
