"""Tests for sorting strategies."""

import pytest

from filemate.file import File
from filemate.directory import Directory
from filemate.node_name_cleaner import NodeNameCleaner
from filemate.sorting_strategies import (
    DefaultStrategy,
    MovieStrategy,
    TVShowStrategy,
    _tokenize_for_matching,
    find_matching_directory,
)


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


# -- _tokenize_for_matching tests --


def test_tokenize_strips_year(cleaner):
    """Year is removed from tokens."""
    tokens = _tokenize_for_matching("The Pitt 2025", cleaner)
    assert tokens == {"the", "pitt"}


def test_tokenize_lowercase(cleaner):
    """Tokens are lowercased."""
    tokens = _tokenize_for_matching("Star Trek", cleaner)
    assert tokens == {"star", "trek"}


def test_tokenize_strips_parenthesized_year(cleaner):
    """Parenthesized year like '(2025)' is stripped."""
    tokens = _tokenize_for_matching("The Pitt (2025)", cleaner)
    assert tokens == {"the", "pitt"}


def test_tokenize_whitespace(cleaner):
    """Extra whitespace is handled."""
    tokens = _tokenize_for_matching("  star   trek  ", cleaner)
    assert tokens == {"star", "trek"}


def test_tokenize_empty_string(cleaner):
    """Empty string gives empty set."""
    tokens = _tokenize_for_matching("", cleaner)
    assert tokens == set()


# -- find_matching_directory tests --


def test_find_matching_exact(tmp_path, cleaner):
    """Exact name match is found."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "The Pitt (2025)").mkdir()
    result = find_matching_directory("the pitt", sorted_dir, cleaner)
    assert result == sorted_dir / "The Pitt (2025)"


def test_find_matching_year_in_existing_dir(tmp_path, cleaner):
    """Candidate without year matches existing dir with year."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "Star Trek Starfleet Academy (2026)").mkdir()
    result = find_matching_directory("star trek starfleet academy", sorted_dir, cleaner)
    assert result == sorted_dir / "Star Trek Starfleet Academy (2026)"


def test_find_matching_reverse_subset(tmp_path, cleaner):
    """Candidate with extra tokens matches existing dir with fewer tokens."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "The Pitt (2025)").mkdir()
    result = find_matching_directory("the pitt 1 00 hmax", sorted_dir, cleaner)
    assert result == sorted_dir / "The Pitt (2025)"


def test_find_matching_best_match(tmp_path, cleaner):
    """When multiple dirs match, pick the one with highest overlap."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "Star Trek").mkdir()
    (sorted_dir / "Star Trek Starfleet Academy").mkdir()
    result = find_matching_directory("star trek starfleet academy", sorted_dir, cleaner)
    assert result == sorted_dir / "Star Trek Starfleet Academy"


def test_find_matching_no_match(tmp_path, cleaner):
    """No matching directory returns None."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "Breaking Bad").mkdir()
    result = find_matching_directory("the pitt", sorted_dir, cleaner)
    assert result is None


def test_find_matching_single_token_guard(tmp_path, cleaner):
    """Single-token overlap with different sets does not match."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "The Office").mkdir()
    # "the" overlaps but that's only 1 token and sets differ
    result = find_matching_directory("the pitt", sorted_dir, cleaner)
    assert result is None


def test_find_matching_single_token_exact(tmp_path, cleaner):
    """Single-token exact match works."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    (sorted_dir / "Silo").mkdir()
    result = find_matching_directory("silo", sorted_dir, cleaner)
    assert result == sorted_dir / "Silo"


def test_find_matching_empty_dir(tmp_path, cleaner):
    """Empty sorted directory returns None."""
    sorted_dir = tmp_path / "TVSHOWS"
    sorted_dir.mkdir()
    result = find_matching_directory("the pitt", sorted_dir, cleaner)
    assert result is None


def test_find_matching_nonexistent_dir(tmp_path, cleaner):
    """Non-existent sorted directory returns None."""
    result = find_matching_directory("the pitt", tmp_path / "NOPE", cleaner)
    assert result is None


def test_find_matching_respect_year_conflict(tmp_path, cleaner):
    """respect_year=True skips dirs with different year."""
    sorted_dir = tmp_path / "MOVIES"
    sorted_dir.mkdir()
    (sorted_dir / "Dune (1984)").mkdir()
    result = find_matching_directory("dune (2021)", sorted_dir, cleaner, respect_year=True)
    assert result is None


def test_find_matching_respect_year_same(tmp_path, cleaner):
    """respect_year=True allows dirs with the same year."""
    sorted_dir = tmp_path / "MOVIES"
    sorted_dir.mkdir()
    (sorted_dir / "Dune (2021)").mkdir()
    result = find_matching_directory("dune (2021)", sorted_dir, cleaner, respect_year=True)
    assert result == sorted_dir / "Dune (2021)"


def test_find_matching_respect_year_candidate_no_year(tmp_path, cleaner):
    """respect_year=True allows match when candidate has no year."""
    sorted_dir = tmp_path / "MOVIES"
    sorted_dir.mkdir()
    (sorted_dir / "Dune (2021)").mkdir()
    result = find_matching_directory("dune", sorted_dir, cleaner, respect_year=True)
    assert result == sorted_dir / "Dune (2021)"


# -- Strategy integration tests with existing dirs --


def test_tvshow_strategy_matches_existing_dir(tmp_path, env_setup, cleaner):
    """TV show file matches existing directory with year suffix."""
    tvshows_dir = tmp_path / "TVSHOWS"
    tvshows_dir.mkdir()
    (tvshows_dir / "The Pitt (2025)").mkdir()

    f = tmp_path / "the pitt s02e05 1100 hmax.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = TVShowStrategy()
    dest = strategy.get_destination(node, tvshows_dir, cleaner)
    assert dest == tvshows_dir / "The Pitt (2025)"


def test_movie_strategy_matches_existing_dir(tmp_path, env_setup, cleaner):
    """Movie file matches existing directory."""
    movies_dir = tmp_path / "MOVIES"
    movies_dir.mkdir()
    (movies_dir / "The Matrix (1999)").mkdir()

    f = tmp_path / "the matrix 1999 remastered.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = MovieStrategy()
    dest = strategy.get_destination(node, movies_dir, cleaner)
    assert dest == movies_dir / "The Matrix (1999)"


def test_tvshow_strategy_no_existing_dir(tmp_path, env_setup, cleaner):
    """TV show with no matching dir creates new path."""
    tvshows_dir = tmp_path / "TVSHOWS"
    tvshows_dir.mkdir()

    f = tmp_path / "brand new show s01e01.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    strategy = TVShowStrategy()
    dest = strategy.get_destination(node, tvshows_dir, cleaner)
    assert dest.parent == tvshows_dir
    assert "brand new show" in str(dest).lower()
