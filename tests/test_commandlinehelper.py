"""Tests for commandlinehelper module."""
import sys
from pathlib import Path

import pytest

# commandlinehelper.py is at project root, not in filemate package
sys.path.insert(0, str(Path(__file__).parent.parent))
from commandlinehelper import parse_args, check_args


def test_parse_args_path(monkeypatch):
    """Path argument is parsed correctly."""
    monkeypatch.setattr("sys.argv", ["main.py", "/some/path"])
    args = parse_args()
    assert args.path == "/some/path"


def test_parse_args_flags(monkeypatch):
    """All boolean flags are parsed correctly."""
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "/some/path", "--sort", "--tree", "--verbose", "--dry-run", "--clean"],
    )
    args = parse_args()
    assert args.sort is True
    assert args.tree is True
    assert args.verbose is True
    assert args.dry_run is True
    assert args.clean is True


def test_parse_args_no_path_exits(monkeypatch):
    """Missing path argument exits with code 2."""
    monkeypatch.setattr("sys.argv", ["main.py"])
    with pytest.raises(SystemExit) as exc_info:
        parse_args()
    assert exc_info.value.code == 2


def test_check_args_valid_path(tmp_path, monkeypatch):
    """Valid path is converted to Path object."""
    monkeypatch.setattr("sys.argv", ["main.py", str(tmp_path)])
    args = parse_args()
    result = check_args(args)
    assert isinstance(result.path, Path)
    assert result.path == tmp_path


def test_check_args_bad_path(monkeypatch):
    """Nonexistent path raises ValueError."""
    monkeypatch.setattr("sys.argv", ["main.py", "/nonexistent/path"])
    args = parse_args()
    with pytest.raises(ValueError, match="Path does not exist"):
        check_args(args)


def test_show_tree_enables_tree(tmp_path, monkeypatch):
    """--show-tree automatically enables --tree."""
    monkeypatch.setattr("sys.argv", ["main.py", str(tmp_path), "--show-tree"])
    args = parse_args()
    result = check_args(args)
    assert result.tree is True
    assert result.show_tree is True
