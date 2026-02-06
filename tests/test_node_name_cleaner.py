"""Tests for NodeNameCleaner."""
from pathlib import Path

from filemate.node_name_cleaner import NodeNameCleaner


def test_cleanup_extra_space():
    """Multiple spaces collapsed to one."""
    assert NodeNameCleaner.cleanup_extra_space("hello   world") == "hello world"
    assert NodeNameCleaner.cleanup_extra_space("  a  b  c  ") == " a b c "


def test_clean_removes_chars(name_cleaner, tmp_path):
    """Characters from clean_chars.txt are replaced with space."""
    f = tmp_path / "file[name].txt"
    f.write_text("x", encoding="utf-8")
    cleaned = name_cleaner.get_cleaned_node_stem(f)
    assert "[" not in cleaned
    assert "]" not in cleaned


def test_clean_removes_words(name_cleaner, tmp_path):
    """Words from clean_words.txt are removed."""
    f = tmp_path / "movie 1080p bluray.mp4"
    f.write_bytes(b"\x00")
    cleaned = name_cleaner.get_cleaned_node_stem(f)
    assert "1080p" not in cleaned
    assert "bluray" not in cleaned


def test_clean_lowercase(name_cleaner, tmp_path):
    """Output is always lowercase."""
    f = tmp_path / "HELLO World.txt"
    f.write_text("x", encoding="utf-8")
    cleaned = name_cleaner.get_cleaned_node_stem(f)
    assert cleaned == cleaned.lower()


def test_get_cleaned_node_stem_file(name_cleaner, tmp_path):
    """File stem is cleaned (no extension)."""
    f = tmp_path / "My Movie.mp4"
    f.write_bytes(b"\x00")
    cleaned = name_cleaner.get_cleaned_node_stem(f)
    assert ".mp4" not in cleaned
    assert "my movie" == cleaned


def test_get_cleaned_node_name_file(name_cleaner, tmp_path):
    """Full name cleaned with extension preserved."""
    f = tmp_path / "My Movie.mp4"
    f.write_bytes(b"\x00")
    cleaned = name_cleaner.get_cleaned_node_name(f)
    assert cleaned.endswith(".mp4")
    assert cleaned == "my movie.mp4"


def test_get_cleaned_node_stem_directory(name_cleaner, tmp_path):
    """Directory name is cleaned (no suffix handling)."""
    d = tmp_path / "My Directory"
    d.mkdir()
    cleaned = name_cleaner.get_cleaned_node_stem(d)
    assert cleaned == "my directory"


def test_year_extraction_present(name_cleaner):
    """Year is extracted from name."""
    assert name_cleaner.get_year_from_node_name("movie 2020") == 2020


def test_year_extraction_absent(name_cleaner):
    """No year returns None."""
    assert name_cleaner.get_year_from_node_name("no year here") is None


def test_year_extraction_19xx(name_cleaner):
    """Older years (19xx) are extracted."""
    assert name_cleaner.get_year_from_node_name("old movie 1985") == 1985


def test_season_episode_sxxeyy(name_cleaner):
    """s01e04 pattern extracts season and episode."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("show s01e04")
    assert season == 1
    assert episode == 4


def test_season_episode_saison(name_cleaner):
    """French 'saison X episode Y' pattern extracts correctly."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("saison 2 episode 3")
    assert season == 2
    assert episode == 3


def test_season_only(name_cleaner):
    """Season-only pattern returns season with None episode."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("show s03")
    assert season == 3
    assert episode is None


def test_episode_only(name_cleaner):
    """Episode-only pattern returns None season with episode."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("show e05")
    assert season is None
    assert episode == 5


def test_no_season_episode(name_cleaner):
    """No pattern returns (None, None)."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("just a movie")
    assert season is None
    assert episode is None


def test_name_without_year(name_cleaner):
    """Year stripped from name."""
    result = name_cleaner.get_name_without_year("movie 2020 title")
    assert "2020" not in result
    assert "movie" in result
    assert "title" in result


def test_season_and_episode_separate(name_cleaner):
    """Separate season and episode patterns in same string."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("s02 stuff e05")
    assert season == 2
    assert episode == 5


def test_season_episode_season_format(name_cleaner):
    """'season 3 episode 7' long-form pattern."""
    season, episode = name_cleaner.get_season_and_episode_from_node_name("season 3 episode 7")
    assert season == 3
    assert episode == 7


def test_name_without_season_episode(name_cleaner):
    """Season/episode stripped from name."""
    result = name_cleaner.get_name_without_season_and_episode("show s01e04 extra")
    assert "s01" not in result.lower()
    assert "e04" not in result.lower()
    assert "show" in result.lower()
    assert "extra" in result.lower()
