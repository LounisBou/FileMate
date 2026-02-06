"""Tests for sorting strategies."""

import pytest

from filemate.file import File
from filemate.directory import Directory
from filemate.node_name_cleaner import NodeNameCleaner
from filemate.sorting_strategies import DefaultStrategy, MovieStrategy, TVShowStrategy


@pytest.fixture()
def cleaner(env_setup):
    """Return a NodeNameCleaner."""
    return NodeNameCleaner()


def test_movie_strategy_with_year(tmp_path, env_setup, cleaner):
    """Movie with year gets 'Title (Year)' subfolder."""
    f = tmp_path / "the matrix 1999.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = MovieStrategy()
    dest = strategy.get_destination(node, tmp_path / "MOVIES", cleaner)
    assert "(1999)" in str(dest)
    assert "MOVIES" in str(dest)


def test_movie_strategy_without_year(tmp_path, env_setup, cleaner):
    """Movie without year uses title-only folder."""
    f = tmp_path / "some movie.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = MovieStrategy()
    dest = strategy.get_destination(node, tmp_path / "MOVIES", cleaner)
    assert "MOVIES" in str(dest)
    assert "some movie" in str(dest).lower()


def test_tvshow_strategy(tmp_path, env_setup, cleaner):
    """TV show gets grouped by show name."""
    f = tmp_path / "my show s01e01.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = TVShowStrategy()
    dest = strategy.get_destination(node, tmp_path / "TVSHOWS", cleaner)
    assert "TVSHOWS" in str(dest)
    # Show name should be stripped of season/episode
    assert "s01" not in str(dest).lower()


def test_default_strategy(tmp_path, env_setup, cleaner):
    """Default strategy returns the sorted dir path directly."""
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = DefaultStrategy()
    dest = strategy.get_destination(node, tmp_path / "AUDIO", cleaner)
    assert dest == tmp_path / "AUDIO"
