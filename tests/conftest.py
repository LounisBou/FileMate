#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixtures and configuration for pytest."""
from pathlib import Path

import pytest

from filemate.node_name_cleaner import NodeNameCleaner


@pytest.fixture()
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture()
def env_setup(monkeypatch, project_root):
    """Set env vars pointing to the real cleaning config files."""
    monkeypatch.setenv("CLEAN_CHARACTERS_FILE", "clean_chars.txt")
    monkeypatch.setenv("CLEAN_WORDS_FILE", "clean_words.txt")


@pytest.fixture()
def sorter_env_setup(monkeypatch, env_setup):
    """Set all sorted directory env vars needed by Sorter."""
    monkeypatch.setenv("MOVIE_DIR", "001-MOVIES")
    monkeypatch.setenv("TVSHOW_DIR", "002-TVSHOWS")
    monkeypatch.setenv("EBOOK_DIR", "003-EBOOKS")
    monkeypatch.setenv("AUDIO_DIR", "004-AUDIO")
    monkeypatch.setenv("APP_DIR", "005-APPS")
    monkeypatch.setenv("ANDROID_DIR", "006-ANDROID")
    monkeypatch.setenv("IMAGE_DIR", "007-IMAGES")
    monkeypatch.setenv("ISO_DIR", "008-ISO")
    monkeypatch.setenv("SCRIPT_DIR", "099-SCRIPTS")


@pytest.fixture()
def sample_file(tmp_path, env_setup):
    """Create a temporary sample file and return its Path."""
    f = tmp_path / "sample.txt"
    f.write_text("hello world", encoding="utf-8")
    return f


@pytest.fixture()
def sample_dir(tmp_path, env_setup):
    """Create a temporary directory with sample files and return its Path."""
    d = tmp_path / "sample_dir"
    d.mkdir()
    (d / "file1.txt").write_text("content1", encoding="utf-8")
    (d / "file2.mp4").write_bytes(b"\x00" * 100)
    (d / "file3.mp3").write_bytes(b"\x00" * 50)
    return d


@pytest.fixture()
def name_cleaner(env_setup):
    """Return a NodeNameCleaner instance."""
    return NodeNameCleaner()
