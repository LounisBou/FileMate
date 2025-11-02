"""Minimal import sanity tests for the generated package."""
import importlib


def test_package_imports() -> None:
    mod = importlib.import_module("youtubetrailerscraper")
    assert hasattr(mod, "__version__")

