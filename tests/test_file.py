"""Tests for the File class."""
import pytest

from filemate.file import File
from filemate.file_type import FileType


def test_file_creation(tmp_path, env_setup):
    """File attributes are populated on creation."""
    f = tmp_path / "test.txt"
    f.write_text("hello", encoding="utf-8")
    node = File(f)
    assert node.name == "test.txt"
    assert node.stem == "test"
    assert node.extension == "txt"
    assert node.path == f.resolve()


def test_file_nonexistent_raises(tmp_path, env_setup):
    """FileNotFoundError for nonexistent path."""
    with pytest.raises(FileNotFoundError):
        File(tmp_path / "does_not_exist.txt")


def test_file_extension_detection(tmp_path, env_setup):
    """Extension is detected correctly."""
    f = tmp_path / "movie.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.extension == "mp4"


def test_file_get_type_movie(tmp_path, env_setup):
    """Video file without season/episode -> MOVIE."""
    f = tmp_path / "the matrix.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.get_type() == FileType.MOVIE


def test_file_get_type_tvshow(tmp_path, env_setup):
    """Video file with season/episode -> TVSHOW."""
    f = tmp_path / "show s01e04.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.get_type() == FileType.TVSHOW


def test_file_get_type_audio(tmp_path, env_setup):
    """Audio file -> AUDIO (regression test for overlap fix)."""
    f = tmp_path / "song.mp3"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.get_type() == FileType.AUDIO


def test_file_get_type_ebook(tmp_path, env_setup):
    """PDF file -> EBOOK."""
    f = tmp_path / "book.pdf"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.get_type() == FileType.EBOOK


def test_file_get_type_other(tmp_path, env_setup):
    """Unknown extension -> OTHER."""
    f = tmp_path / "file.xyz"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    assert node.get_type() == FileType.OTHER


def test_file_equality_by_name(tmp_path, env_setup):
    """Two File objects with same name share the same hash (hash is by name)."""
    f1 = tmp_path / "sub1"
    f1.mkdir()
    f2 = tmp_path / "sub2"
    f2.mkdir()
    (f1 / "same.txt").write_text("a", encoding="utf-8")
    (f2 / "same.txt").write_text("b", encoding="utf-8")
    node1 = File(f1 / "same.txt")
    node2 = File(f2 / "same.txt")
    assert node1.name == node2.name
    # Hash is based on name per FileSystemNode.__hash__
    assert hash(node1) == hash(node2)


def test_file_size_comparison(tmp_path, env_setup):
    """Smaller file < larger file."""
    small = tmp_path / "small.txt"
    small.write_bytes(b"\x00" * 10)
    large = tmp_path / "large.txt"
    large.write_bytes(b"\x00" * 1000)
    node_small = File(small)
    node_small.size = small.stat().st_size
    node_large = File(large)
    node_large.size = large.stat().st_size
    assert node_small < node_large


def test_file_bool_truthy(tmp_path, env_setup):
    """Non-empty file is truthy when size is set."""
    f = tmp_path / "nonempty.txt"
    f.write_text("content", encoding="utf-8")
    node = File(f)
    node.size = f.stat().st_size
    assert bool(node)


def test_file_bool_falsy(tmp_path, env_setup):
    """Empty file is falsy."""
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    node = File(f)
    # size defaults to 0 for empty file
    assert not bool(node)


def test_file_contains(tmp_path, env_setup):
    """String in file stem is detected."""
    f = tmp_path / "my_keyword_file.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    assert "keyword" in node


def test_file_delete(tmp_path, env_setup):
    """File is removed from disk."""
    f = tmp_path / "to_delete.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    node.delete()
    assert not f.exists()


def test_file_rename(tmp_path, env_setup):
    """File is renamed correctly."""
    f = tmp_path / "old_name.txt"
    f.write_text("x", encoding="utf-8")
    node = File(f)
    node.rename("new_name.txt")
    assert node.name == "new_name.txt"
    assert node.path.exists()
    assert not f.exists()


def test_file_move(tmp_path, env_setup):
    """File is moved to new location."""
    f = tmp_path / "moveme.txt"
    f.write_text("x", encoding="utf-8")
    dest = tmp_path / "subdir" / "moveme.txt"
    node = File(f)
    node.move(dest)
    assert dest.exists()
    assert not f.exists()


def test_file_pack(tmp_path, env_setup):
    """File is wrapped in a same-named directory."""
    f = tmp_path / "packme.mp4"
    f.write_bytes(b"\x00" * 10)
    node = File(f)
    pack_dir = node.pack()
    assert pack_dir.is_dir()
    assert pack_dir.name == "packme"
    assert (pack_dir / "packme.mp4").exists()
