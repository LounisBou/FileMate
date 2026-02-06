"""CLI sanity tests using the top-level script."""
from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "main.py", *args], text=True, capture_output=True)


def test_cli_help() -> None:
    cp = run_cli("-h")
    assert cp.returncode == 0
    assert "usage" in cp.stdout.lower() or "help" in cp.stdout.lower()


def test_cli_missing_path() -> None:
    """Missing required path argument should exit with code 2."""
    cp = run_cli()
    assert cp.returncode == 2


def test_cli_nonexistent_path() -> None:
    """Providing a nonexistent path should error."""
    cp = run_cli("/nonexistent/path/that/does/not/exist")
    assert cp.returncode != 0
