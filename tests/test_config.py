"""Tests for AppSettings configuration."""

import pytest
from pydantic import ValidationError

from filemate.config import AppSettings


def test_settings_defaults(env_setup):
    """Defaults load from env variables."""
    settings = AppSettings()
    assert settings.clean_characters_file.name == "clean_chars.txt"
    assert settings.clean_words_file.name == "clean_words.txt"
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379
    assert settings.redis_db == 0


def test_settings_missing_file_raises(tmp_path, monkeypatch):
    """Missing cleaning config file raises ValidationError."""
    monkeypatch.setenv("CLEAN_CHARACTERS_FILE", str(tmp_path / "nonexistent.txt"))
    monkeypatch.setenv("CLEAN_WORDS_FILE", "clean_words.txt")
    with pytest.raises(ValidationError, match="Cleaning config file not found"):
        AppSettings()


def test_settings_sorted_dirs(sorter_env_setup):
    """Sorted directory names are populated from env."""
    settings = AppSettings()
    assert settings.movie_dir == "001-MOVIES"
    assert settings.tvshow_dir == "002-TVSHOWS"
    assert settings.audio_dir == "004-AUDIO"
    dirs = settings.sorted_dir_names
    assert "movie_dir" in dirs
    assert dirs["movie_dir"] == "001-MOVIES"


def test_redis_config_property(env_setup):
    """redis_config returns dict with host/port/db."""
    settings = AppSettings()
    rc = settings.redis_config
    assert isinstance(rc, dict)
    assert rc["host"] == "localhost"
    assert rc["port"] == 6379
    assert rc["db"] == 0


def test_settings_sorted_dirs_none_excluded(env_setup):
    """sorted_dir_names excludes None values."""
    settings = AppSettings()
    dirs = settings.sorted_dir_names
    assert all(v is not None for v in dirs.values())
