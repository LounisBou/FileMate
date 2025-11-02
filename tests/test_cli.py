"""Minimal CLI sanity tests using the top-level script."""
from __future__ import annotations

import subprocess
import sys


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "main.py", *args], text=True, capture_output=True)


def test_cli_help() -> None:
    cp = run_cli("-h")
    assert cp.returncode == 0
    assert "usage" in cp.stdout.lower() or "help" in cp.stdout.lower()


def test_cli_runs_default() -> None:
    cp = run_cli()
    assert cp.returncode == 0
    # Placeholder output from template CLI
    assert "placeholder" in cp.stdout.lower()

