"""Import sanity tests for the filemate package."""
import importlib


def test_package_imports() -> None:
    """Key classes are importable from the filemate package."""
    mod = importlib.import_module("filemate")
    assert hasattr(mod, "File")
    assert hasattr(mod, "Directory")
    assert hasattr(mod, "FileType")
    assert hasattr(mod, "FileTypeExtensions")
    assert hasattr(mod, "FileSystemNode")
    assert hasattr(mod, "FileSystemNodeFactory")
    assert hasattr(mod, "NodeNameCleaner")
    assert hasattr(mod, "Sorter")


def test_version_available() -> None:
    """Package exposes __version__ from _about.py."""
    from filemate._about import __version__

    assert __version__ == "0.0.1"
