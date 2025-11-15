"""
Repository Pattern Implementations

Abstractions for data access and caching.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .interfaces import IPlaylistReader
from .models import PlaylistMetadata
from .playlist_cache import PlaylistCache

logger = logging.getLogger(__name__)


class IPlaylistRepository(ABC):
    """Interface for playlist repository (Repository Pattern)."""

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Dict]:
        """
        Find playlist by name.

        Args:
            name: Playlist name

        Returns:
            Playlist data or None if not found
        """
        pass

    @abstractmethod
    def find_by_id(self, playlist_id: str) -> Optional[Dict]:
        """
        Find playlist by ID.

        Args:
            playlist_id: Playlist ID

        Returns:
            Playlist data or None if not found
        """
        pass

    @abstractmethod
    def save(self, playlist: Dict) -> None:
        """
        Save playlist to repository.

        Args:
            playlist: Playlist data
        """
        pass

    @abstractmethod
    def get_all(self, limit: int = 50) -> List[Dict]:
        """
        Get all playlists.

        Args:
            limit: Maximum number of playlists

        Returns:
            List of playlist data
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear cached playlist data."""
        pass


class CachedPlaylistRepository(IPlaylistRepository):
    """
    Playlist repository with caching support.

    Implements Repository Pattern with caching layer.
    """

    def __init__(self, playlist_reader: IPlaylistReader, cache: Optional[PlaylistCache] = None):
        """
        Initialize repository.

        Args:
            playlist_reader: Reader for fetching playlists from Spotify
            cache: Optional cache for storing playlist data
        """
        self._reader = playlist_reader
        self._cache = cache or PlaylistCache()
        self._all_playlists_cache: Optional[List[Dict]] = None

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find playlist by name with caching."""
        # Check cache first
        cached = self._cache.get(name)
        if cached:
            logger.debug(f"Cache hit for playlist: {name}")
            return cached

        # Cache miss - fetch all playlists
        logger.debug(f"Cache miss for playlist: {name}")
        all_playlists = self.get_all()

        # Search for playlist by name
        for playlist in all_playlists:
            if playlist["name"] == name:
                # Update cache
                self._cache.set(name, playlist)
                return playlist

        return None

    def find_by_id(self, playlist_id: str) -> Optional[Dict]:
        """Find playlist by ID."""
        # If we have all playlists cached, search there
        if self._all_playlists_cache:
            for playlist in self._all_playlists_cache:
                if playlist["id"] == playlist_id:
                    return playlist

        # Otherwise, fetch all and search
        all_playlists = self.get_all()
        for playlist in all_playlists:
            if playlist["id"] == playlist_id:
                return playlist

        return None

    def save(self, playlist: Dict) -> None:
        """Save playlist to cache."""
        name = playlist.get("name")

        if name:
            self._cache.set(name, playlist)
            logger.debug(f"Cached playlist: {name}")

        # Invalidate all playlists cache
        self._all_playlists_cache = None

    def get_all(self, limit: int = 50) -> List[Dict]:
        """Get all playlists with caching."""
        # Return cached if available
        if self._all_playlists_cache is not None:
            logger.debug("Returning cached playlist list")
            return self._all_playlists_cache[:limit]

        # Fetch from Spotify
        logger.debug("Fetching playlists from Spotify API")
        playlists = []
        result = self._reader.current_user_playlists(limit=limit)

        while result and len(playlists) < limit:
            items = result.get("items", [])
            playlists.extend(items)

            if len(playlists) >= limit or not result.get("next"):
                break

            result = self._reader.next(result)

        # Cache the results
        self._all_playlists_cache = playlists

        # Also cache individual playlists
        for playlist in playlists:
            name = playlist.get("name")
            if name:
                self._cache.set(name, playlist)

        return playlists[:limit]

    def clear_cache(self) -> None:
        """Clear all cached data."""
        logger.info("Clearing playlist cache")
        self._all_playlists_cache = None
        # Note: PlaylistCache doesn't have a clear method, so we create a new instance
        self._cache = PlaylistCache()
