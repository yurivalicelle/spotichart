"""
Playlist Cache Module

Handles caching of playlist data following Single Responsibility Principle.
"""

import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class PlaylistCache:
    """Manages caching of playlist information."""

    def __init__(self, cache_file: Optional[Path] = None, ttl_hours: int = 24):
        """
        Initialize playlist cache.

        Args:
            cache_file: Path to cache file (if None, uses in-memory cache only)
            ttl_hours: Time to live for cache entries in hours
        """
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, Dict] = {}

        if cache_file:
            self._load_from_file()

    def _load_from_file(self) -> None:
        """Load cache from file if it exists."""
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)

            # Filter out expired entries
            now = datetime.now()
            for key, value in cache_data.items():
                cached_at = datetime.fromisoformat(value.get("cached_at", ""))
                if now - cached_at < self.ttl:
                    self._cache[key] = value["playlist"]

            logger.info(f"Loaded {len(self._cache)} entries from cache file")

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to load cache from file: {str(e)}")
            self._cache = {}

    def _save_to_file(self) -> None:
        """Save cache to file."""
        if not self.cache_file:
            return

        try:
            # Ensure parent directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            now = datetime.now().isoformat()
            cache_data = {
                key: {"playlist": value, "cached_at": now} for key, value in self._cache.items()
            }

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

            logger.debug(f"Saved {len(self._cache)} entries to cache file")

        except Exception as e:
            logger.warning(f"Failed to save cache to file: {str(e)}")

    def get(self, name: str) -> Optional[Dict]:
        """
        Get playlist from cache by name.

        Args:
            name: Playlist name (case-insensitive)

        Returns:
            Playlist data if found and not expired, None otherwise
        """
        cache_key = name.lower().strip()
        playlist = self._cache.get(cache_key)

        if playlist:
            logger.debug(f"Cache hit for playlist: {name}")
        else:
            logger.debug(f"Cache miss for playlist: {name}")

        return playlist

    def set(self, name: str, playlist: Dict) -> None:
        """
        Add or update playlist in cache.

        Args:
            name: Playlist name
            playlist: Playlist data to cache
        """
        cache_key = name.lower().strip()
        self._cache[cache_key] = playlist
        logger.debug(f"Added playlist to cache: {name}")

        # Save to file if configured
        if self.cache_file:
            self._save_to_file()

    def remove(self, name: str) -> None:
        """
        Remove playlist from cache.

        Args:
            name: Playlist name to remove
        """
        cache_key = name.lower().strip()
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug(f"Removed playlist from cache: {name}")

            # Update file if configured
            if self.cache_file:
                self._save_to_file()

    def clear(self) -> None:
        """Clear all entries from cache."""
        self._cache.clear()
        logger.info("Cleared all cache entries")

        if self.cache_file:
            self._save_to_file()

    def contains(self, name: str) -> bool:
        """
        Check if playlist is in cache.

        Args:
            name: Playlist name to check

        Returns:
            True if playlist is in cache, False otherwise
        """
        cache_key = name.lower().strip()
        return cache_key in self._cache
