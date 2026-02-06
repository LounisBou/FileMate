"""Centralized application settings loaded from environment and .env file."""

from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-wide configuration loaded from environment variables and .env file.

    Attributes:
        clean_characters_file: Path to the file containing characters to strip.
        clean_words_file: Path to the file containing words to strip.
        movie_dir: Destination directory name for movies.
        tvshow_dir: Destination directory name for TV shows.
        ebook_dir: Destination directory name for ebooks.
        audio_dir: Destination directory name for audio files.
        app_dir: Destination directory name for applications.
        android_dir: Destination directory name for Android APKs.
        image_dir: Destination directory name for images.
        iso_dir: Destination directory name for ISO disc images.
        script_dir: Destination directory name for scripts.
        redis_host: Redis server hostname.
        redis_port: Redis server port.
        redis_db: Redis database number.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Cleaning config
    clean_characters_file: Path = Path("clean_chars.txt")
    clean_words_file: Path = Path("clean_words.txt")

    # Sorted directory names (all optional — only needed when sorting)
    movie_dir: Optional[str] = None
    tvshow_dir: Optional[str] = None
    ebook_dir: Optional[str] = None
    audio_dir: Optional[str] = None
    app_dir: Optional[str] = None
    android_dir: Optional[str] = None
    image_dir: Optional[str] = None
    iso_dir: Optional[str] = None
    script_dir: Optional[str] = None

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @field_validator("clean_characters_file", "clean_words_file")
    @classmethod
    def _check_file_exists(cls, v: Path) -> Path:
        """Validate that the cleaning config file exists.

        Args:
            v: The file path to validate.

        Returns:
            The validated path.

        Raises:
            ValueError: If the file does not exist.
        """
        if not v.exists():
            raise ValueError(f"Cleaning config file not found: {v}")
        return v

    @property
    def redis_config(self) -> dict:
        """Return Redis connection parameters as a dict.

        Returns:
            Dictionary with host, port, and db keys.
        """
        return {"host": self.redis_host, "port": self.redis_port, "db": self.redis_db}

    @property
    def sorted_dir_names(self) -> dict:
        """Return a mapping of dir-type env var names to their configured values.

        Returns:
            Dictionary mapping setting names to directory name strings (non-None only).
        """
        names = {
            "movie_dir": self.movie_dir,
            "tvshow_dir": self.tvshow_dir,
            "ebook_dir": self.ebook_dir,
            "audio_dir": self.audio_dir,
            "app_dir": self.app_dir,
            "android_dir": self.android_dir,
            "image_dir": self.image_dir,
            "iso_dir": self.iso_dir,
            "script_dir": self.script_dir,
        }
        return {k: v for k, v in names.items() if v is not None}
