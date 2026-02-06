# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FileMate is a Python CLI tool for organizing media files into categorized directories. It detects file types by extension, cleans filenames (removing unwanted characters/words), extracts metadata (year, season/episode), and sorts files into configurable destination folders (movies, TV shows, ebooks, audio, etc.).

## Commands

```bash
# Run the tool
python main.py /path/to/directory --sort --verbose --dry-run

# Run tests
pytest
pytest tests/test_cli.py          # single file
pytest --cov                      # with coverage

# Code formatting (line length: 99)
black filemate/
isort filemate/

# Linting / type checking
pylint filemate/
flake8 filemate/
mypy filemate/
```

## Architecture

### Entry Point & CLI

`main.py` is the entry point. `commandlinehelper.py` handles argument parsing (`parse_args`), validation (`check_args`), and defaults (`set_default_args_values`). It also provides colored terminal output utilities (`print_message`).

### Core Class Hierarchy (all in `filemate/`)

**`FileSystemNode`** (ABC, dataclass) is the base for all filesystem objects. It wraps a `pathlib.Path` and automatically computes cleaned names via `NodeNameCleaner` on init. Equality/hashing is by name; comparison operators (`<`, `>`, etc.) compare by size. Provides `move()`, `rename()`, `copy()`, `delete()` filesystem operations.

**`File(FileSystemNode)`** adds extension detection and type resolution. `get_type()` maps extension -> `FileTypeExtensions` enum -> `FileType` enum, with special logic: VIDEO files with season/episode patterns in the name become `TVSHOW`, otherwise `MOVIE`. Has a `pack()` method to wrap a file in a same-named directory.

**`Directory(FileSystemNode)`** supports iteration (`iter()`, `iter_files()`, `iter_dir()`), containment checks, subscript access (`dir['file.txt']`), and operator overloads: `/` for path join, `**` for merge, `%` for mkdir, `&` for intersection, `|` for union. `get_type()` determines directory type by majority file type of its contents. Has `unpack()` to move contents to parent.

### Type System

**`FileType`** (Enum): semantic types — MOVIE, TVSHOW, EBOOK, AUDIO, APP, ANDROID, IMAGE, ISO, SCRIPT, SUBTITLE, DOCUMENT, OTHER.

**`FileTypeExtensions`** (Enum): maps each type to a list of file extensions. `get_file_type(extension)` resolves extension to type. Note: VIDEO is an extension category that gets resolved to MOVIE or TVSHOW in `File.get_type()`.

### Sorting Engine

**`Sorter`** reads destination directory names from `.env` via `python-dotenv` (e.g., `MOVIE_DIR="001-MOVIES"`). The `process()` method iterates children of the root node and calls `sort()` on each. Sort logic determines destination paths with special handling:
- Movies: creates `"Movie Title (Year)"` subdirectories
- TV Shows: groups by show name (strips season/episode info)
- Supports `dry_run` mode and `delete_remaining_element` cleanup

### Filename Cleaning

**`NodeNameCleaner`** loads character and word lists from files specified in `.env` (`clean_chars.txt`, `clean_words.txt`). Cleaning pipeline: lowercase -> strip -> remove chars -> remove words (regex word boundaries) -> collapse whitespace. Also extracts years (`19xx`/`20xx`) and season/episode patterns (`s01e04`, `saison 1 episode 4`).

### Tree & Packer

**`FileSystemNodeTree`** builds a hierarchical tree using `bigtree.Node`, with Redis caching via `pymate.CacheIt`. Supports save/restore to JSON, search by name/path, and tree visualization.

**`Packer`** transfers nodes between two `FileSystemNodeTree` instances with override, merge, or replace strategies.

### Factory

**`FileSystemNodeFactory.create_node(path)`** returns a `File` or `Directory` based on whether the path is a file or directory.

## Configuration

The `.env` file (template: `.env-example`) defines:
- Destination directory names per file type (`MOVIE_DIR`, `TVSHOW_DIR`, etc.)
- Cleaning config file paths (`CLEAN_WORDS_FILE`, `CLEAN_CHARACTERS_FILE`)

## Dependencies

Key runtime dependencies: `bigtree`, `python-dotenv`, `pymate` (provides `LogIt`, `CacheIt`, `SaveIt`, `TimeIt`), `termcolor`. Python >= 3.9 (`.python-version` specifies 3.10.9).

## Notes

- The `pyproject.toml` and `setup.py` still reference a template project name ("youtubetrailerscraper") and a `src/` layout, but the actual code lives directly in `filemate/` (flat layout).
- Tests in `tests/` are currently minimal scaffolding from the template; `test_import.py` references the old package name.
- `conftest.py` adds `src/` to `sys.path` but the package is at `filemate/`, not `src/filemate/`.
