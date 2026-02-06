#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Enum defining semantic file types used for sorting and classification."""

from enum import Enum


class FileType(Enum):
    """
    Enum class for file types.
    """
    VIDEO = "video"       # Generic video (resolved to MOVIE or TVSHOW by File.get_type)
    MOVIE = "movie"       # Video without season/episode info
    TVSHOW = "tvshow"     # Video with season/episode info
    EBOOK = "ebook"       # PDF, EPUB, MOBI, etc.
    AUDIO = "audio"       # MP3, FLAC, WAV, etc.
    APP = "app"           # Executables, installers
    ANDROID = "android"   # APK files
    ARCHIVE = "archive"   # ZIP, RAR, 7z, etc.
    IMAGE = "image"       # JPG, PNG, GIF, etc.
    SUBTITLE = "subtitle" # SRT, SUB, VTT, etc.
    DOCUMENT = "document" # DOC, XLSX, PPT, etc.
    ISO = "iso"           # Disc images
    SCRIPT = "script"     # Source code, config files
    OTHER = "other"       # Anything else
