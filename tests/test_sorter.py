"""Tests for the Sorter class."""
import pytest

from filemate.directory import Directory
from filemate.file import File
from filemate.file_type import FileType
from filemate.sorter import Sorter


def _create_sorted_dirs(root):
    """Create the expected sorted directories inside root."""
    for name in [
        "001-MOVIES", "002-TVSHOWS", "003-EBOOKS", "004-AUDIO",
        "005-APPS", "006-ANDROID", "007-IMAGES", "008-ISO", "099-SCRIPTS",
    ]:
        (root / name).mkdir(exist_ok=True)


def test_sorter_init(tmp_path, sorter_env_setup):
    """Sorted dir names are loaded from env."""
    d = tmp_path / "root"
    d.mkdir()
    _create_sorted_dirs(d)
    root = Directory(d)
    sorter = Sorter(root)
    assert sorter.sorted_dir_names[FileType.MOVIE] == "001-MOVIES"
    assert sorter.sorted_dir_names[FileType.TVSHOW] == "002-TVSHOWS"
    assert sorter.sorted_dir_names[FileType.AUDIO] == "004-AUDIO"


def test_sorter_is_sorted_dir(tmp_path, sorter_env_setup):
    """Sorter recognizes sorted directories."""
    d = tmp_path / "root2"
    d.mkdir()
    _create_sorted_dirs(d)
    root = Directory(d)
    sorter = Sorter(root)
    movies_dir = Directory(d / "001-MOVIES")
    # _Sorter__is_sorted_dir is name-mangled private method
    assert sorter._Sorter__is_sorted_dir(movies_dir) is True


def test_sorter_movie_dest_with_year(tmp_path, sorter_env_setup):
    """Movie with year gets destination like 'movies/The matrix (1999)/'."""
    d = tmp_path / "root3"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "the matrix 1999.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    dest = sorter._Sorter__get_node_destination_path(file_node)
    assert "001-MOVIES" in str(dest)
    assert "(1999)" in str(dest)


def test_sorter_movie_dest_without_year(tmp_path, sorter_env_setup):
    """Movie without year uses cleaned stem as folder name."""
    d = tmp_path / "root4"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "some movie.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    dest = sorter._Sorter__get_node_destination_path(file_node)
    assert "001-MOVIES" in str(dest)


def test_sorter_tvshow_dest(tmp_path, sorter_env_setup):
    """TV show file gets grouped by show name."""
    d = tmp_path / "root5"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "show s01e01.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    dest = sorter._Sorter__get_node_destination_path(file_node)
    assert "002-TVSHOWS" in str(dest)


def test_sorter_dry_run(tmp_path, sorter_env_setup):
    """Dry run does not move files."""
    d = tmp_path / "root6"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "dryrun movie.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root, dry_run=True)
    file_node = File(f)
    sorter.sort(file_node)
    # File should still be in original location
    assert f.exists()


def test_sorter_sort_movie(tmp_path, sorter_env_setup):
    """File ends up in the movie directory."""
    d = tmp_path / "root7"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "test movie.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    sorter.sort(file_node)
    # File should no longer be in original location
    assert not f.exists()
    # File should be somewhere under 001-MOVIES
    movies = d / "001-MOVIES"
    found = list(movies.rglob("*.mp4"))
    assert len(found) >= 1


def test_sorter_sort_skips_sorted_dir(tmp_path, sorter_env_setup):
    """Already-sorted directories are skipped."""
    d = tmp_path / "root8"
    d.mkdir()
    _create_sorted_dirs(d)
    root = Directory(d)
    sorter = Sorter(root)
    movies_dir = Directory(d / "001-MOVIES")
    # Should be a no-op (no error)
    sorter.sort(movies_dir)


def test_sorter_process(tmp_path, sorter_env_setup):
    """Process sorts multiple files correctly."""
    d = tmp_path / "root9"
    d.mkdir()
    _create_sorted_dirs(d)
    (d / "movie one.mp4").write_bytes(b"\x00" * 10)
    (d / "song.mp3").write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    sorter.process()
    # Both files should have been moved
    assert not (d / "movie one.mp4").exists()
    assert not (d / "song.mp3").exists()
    # Movie in movies dir
    assert len(list((d / "001-MOVIES").rglob("*.mp4"))) >= 1
    # Audio in audio dir
    assert len(list((d / "004-AUDIO").rglob("*.mp3"))) >= 1


def test_sorter_check_node_type_disallowed(tmp_path, sorter_env_setup):
    """Disallowed type (e.g. ARCHIVE) returns None."""
    d = tmp_path / "root_dis"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "archive.zip"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    result = sorter._Sorter__check_node_type(file_node)
    assert result is None


def test_sorter_check_node_type_no_sorted_dir(tmp_path, sorter_env_setup):
    """Type with no sorted dir configured returns None."""
    d = tmp_path / "root_nosort"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "sub.srt"
    f.write_text("subtitle", encoding="utf-8")
    root = Directory(d)
    sorter = Sorter(root)
    file_node = File(f)
    result = sorter._Sorter__check_node_type(file_node)
    assert result is None


def test_sorter_movie_dir_sort(tmp_path, sorter_env_setup):
    """Movie directory node is sorted (renamed and moved)."""
    d = tmp_path / "root_mdir"
    d.mkdir()
    _create_sorted_dirs(d)
    movie_dir = d / "the matrix 1999"
    movie_dir.mkdir()
    (movie_dir / "the matrix.mp4").write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    dir_node = Directory(movie_dir)
    sorter.sort(dir_node)
    # Directory should have been moved to 001-MOVIES
    found = list((d / "001-MOVIES").iterdir())
    assert len(found) >= 1


def test_sorter_movie_dir_dry_run(tmp_path, sorter_env_setup):
    """Movie directory in dry run mode logs but doesn't rename."""
    d = tmp_path / "root_mdir_dry"
    d.mkdir()
    _create_sorted_dirs(d)
    movie_dir = d / "the matrix 1999"
    movie_dir.mkdir()
    (movie_dir / "the matrix.mp4").write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root, dry_run=True)
    dir_node = Directory(movie_dir)
    sorter.sort(dir_node)
    # Original dir should still exist (dry run)
    assert movie_dir.exists()


def test_sorter_tvshow_dir_elements(tmp_path, sorter_env_setup):
    """TV show directory: individual episodes are sorted."""
    d = tmp_path / "root_tvdir"
    d.mkdir()
    _create_sorted_dirs(d)
    show_dir = d / "my show"
    show_dir.mkdir()
    (show_dir / "my show s01e01.mp4").write_bytes(b"\x00" * 10)
    (show_dir / "my show s01e02.mp4").write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    dir_node = Directory(show_dir)
    sorter.sort(dir_node)
    # Episodes should be under 002-TVSHOWS
    found = list((d / "002-TVSHOWS").rglob("*.mp4"))
    assert len(found) >= 2


def test_sorter_process_single_file(tmp_path, sorter_env_setup):
    """process() sorts a directory with a single file."""
    d = tmp_path / "root_single"
    d.mkdir()
    _create_sorted_dirs(d)
    f = d / "solo movie.mp4"
    f.write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root)
    sorter.process()
    assert not f.exists()
    assert len(list((d / "001-MOVIES").rglob("*.mp4"))) >= 1


def test_sorter_process_verbose(tmp_path, sorter_env_setup):
    """process() with verbose=True does not crash."""
    d = tmp_path / "root_verbose"
    d.mkdir()
    _create_sorted_dirs(d)
    (d / "verbose movie.mp4").write_bytes(b"\x00" * 10)
    root = Directory(d)
    sorter = Sorter(root, verbose=True)
    sorter.process()
