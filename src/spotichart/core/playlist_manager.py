"""
Playlist Manager Module

Manages Spotify playlist operations following SOLID principles.
"""

import logging
from pathlib import Path
from typing import Optional
from .interfaces import IPlaylistOperations, ISpotifyClient
from .playlist_cache import PlaylistCache
from ..utils.exceptions import PlaylistCreationError

logger = logging.getLogger(__name__)


class PlaylistManager(IPlaylistOperations):
    """
    Manages Spotify playlist operations.
    Implements IPlaylistOperations and depends on ISpotifyClient abstraction.
    """

    def __init__(
        self,
        client: ISpotifyClient,
        cache: Optional[PlaylistCache] = None,
        cache_file: Optional[Path] = None,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize playlist manager with dependency injection.

        Args:
            client: Spotify client interface
            cache: Optional pre-configured cache instance
            cache_file: Path to cache file (used if cache is not provided)
            cache_ttl_hours: Cache TTL in hours (used if cache is not provided)
        """
        self.client = client

        # Use provided cache or create new one
        if cache is not None:
            self.cache = cache
        else:
            # Default cache file location if not specified
            if cache_file is None:
                cache_file = Path.home() / '.spotichart' / 'cache' / 'playlists.json'
            self.cache = PlaylistCache(cache_file=cache_file, ttl_hours=cache_ttl_hours)

    def create(self, name: str, description: str, public: bool = False):
        """
        Create a new playlist.

        Args:
            name: Playlist name
            description: Playlist description
            public: Whether playlist is public

        Returns:
            Playlist information dictionary

        Raises:
            PlaylistCreationError: If playlist creation fails
        """
        try:
            logger.info(f"Creating playlist: {name}")
            user_id = self.client.user_id

            playlist = self.client.user_playlist_create(
                user=user_id,
                name=name,
                public=public,
                description=description
            )

            # Add to cache
            self.cache.set(name, playlist)
            logger.info(f"Playlist created successfully: {playlist['id']}")

            return playlist

        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise PlaylistCreationError(f"Playlist creation failed: {e}") from e

    def find_by_name(self, name: str):
        """
        Find a playlist by name in user's library.

        Args:
            name: Playlist name to search for

        Returns:
            Playlist dictionary if found, None otherwise
        """
        logger.info(f"Searching for playlist: '{name}'")

        # Check cache first
        cached_playlist = self.cache.get(name)
        if cached_playlist:
            logger.info(f"Found playlist in cache: {cached_playlist['id']}")
            return cached_playlist

        # Search through user's playlists
        offset = 0
        limit = 50
        checked_count = 0

        try:
            while True:
                playlists = self.client.current_user_playlists(limit=limit, offset=offset)

                for item in playlists['items']:
                    checked_count += 1
                    playlist_name = item['name']
                    logger.debug(f"Checking playlist #{checked_count}: '{playlist_name}'")

                    if playlist_name.lower().strip() == name.lower().strip():
                        logger.info(f"Found existing playlist: {item['id']} - '{playlist_name}'")
                        # Add to cache for future lookups
                        self.cache.set(name, item)
                        return item

                # Check if there are more playlists
                if not playlists.get('next'):
                    break

                offset += limit

            logger.info(f"Playlist '{name}' not found after checking {checked_count} playlists")
            return None

        except Exception as e:
            logger.error(f"Error searching for playlist: {str(e)}")
            return None

    def clear(self, playlist_id: str):
        """
        Remove all tracks from a playlist.

        Args:
            playlist_id: Playlist ID to clear

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Clearing playlist: {playlist_id}")

            # Get all tracks
            tracks = []
            results = self.client.playlist_tracks(playlist_id)
            tracks.extend(results['items'])

            while results.get('next'):
                results = self.client.next(results)
                tracks.extend(results['items'])

            # Extract track URIs
            track_uris = [item['track']['uri'] for item in tracks if item.get('track')]

            # Remove in batches of 100
            if track_uris:
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i + 100]
                    self.client.playlist_remove_all_occurrences_of_items(playlist_id, batch)
                    logger.debug(f"Removed batch {i // 100 + 1}")

            logger.info(f"Cleared {len(track_uris)} tracks from playlist")
            return True

        except Exception as e:
            logger.error(f"Failed to clear playlist: {str(e)}")
            return False

    def update_details(self, playlist_id: str, description: str):
        """
        Update playlist details.

        Args:
            playlist_id: Playlist ID
            description: New description

        Returns:
            True if successful, False otherwise
        """
        if not description:
            logger.warning("No description provided for update")
            return False

        try:
            logger.info(f"Updating playlist details: {playlist_id}")
            self.client.playlist_change_details(playlist_id, description=description)
            logger.info("Playlist details updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to update playlist details: {str(e)}")
            return False

    def get_all(self, limit: int = 50):
        """
        Get user's playlists.

        Args:
            limit: Maximum number of playlists to retrieve

        Returns:
            List of playlist dictionaries
        """
        try:
            logger.info(f"Fetching user playlists (limit={limit})")
            result = self.client.current_user_playlists(limit=limit)
            playlists = result.get('items', [])
            logger.info(f"Retrieved {len(playlists)} playlists")
            return playlists

        except Exception as e:
            logger.error(f"Failed to get playlists: {str(e)}")
            return []
