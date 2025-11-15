"""
Track Manager Module

Manages Spotify track operations following SOLID principles.
"""

import logging
from .interfaces import ITrackOperations, ISpotifyClient
from ..utils.exceptions import TrackAdditionError

logger = logging.getLogger(__name__)


class TrackManager(ITrackOperations):
    """
    Manages Spotify track operations.
    Implements ITrackOperations and depends on ISpotifyClient abstraction.
    """

    def __init__(self, client: ISpotifyClient):
        """
        Initialize track manager with dependency injection.

        Args:
            client: Spotify client interface
        """
        self.client = client

    def build_uri(self, track_id: str) -> str:
        """
        Build Spotify track URI from track ID.

        Args:
            track_id: Spotify track ID

        Returns:
            Formatted Spotify track URI
        """
        return f"spotify:track:{track_id}"

    def add_to_playlist(self, playlist_id: str, track_uris: list) -> int:
        """
        Add tracks to a playlist in batches.

        Args:
            playlist_id: Playlist ID
            track_uris: List of track URIs to add

        Returns:
            Number of tracks successfully added

        Raises:
            TrackAdditionError: If adding tracks fails
        """
        if not track_uris:
            logger.warning("No track URIs provided")
            return 0

        try:
            logger.info(f"Adding {len(track_uris)} tracks to playlist {playlist_id}")
            added_count = 0

            # Add tracks in batches of 100 (Spotify API limit)
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                self.client.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                logger.debug(f"Added batch {i // batch_size + 1}: {len(batch)} tracks")

            logger.info(f"Successfully added {added_count} tracks to playlist")
            return added_count

        except Exception as e:
            logger.error(f"Failed to add tracks to playlist: {str(e)}")
            raise TrackAdditionError(f"Failed to add tracks: {e}") from e
