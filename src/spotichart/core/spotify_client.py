"""
Spotify Client Module

Simplified client that implements ISpotifyClient interface.
Follows Dependency Inversion Principle by depending on abstractions.
"""

import logging
from typing import List, Dict, Optional
import spotipy
from .interfaces import ISpotifyClient
from .spotify_authenticator import SpotifyAuthenticator

logger = logging.getLogger(__name__)


class SpotifyClient(ISpotifyClient):
    """
    Wrapper class for Spotify API interactions.
    Implements ISpotifyClient interface and delegates to SpotifyAuthenticator.
    """

    def __init__(self, authenticator: SpotifyAuthenticator):
        """
        Initialize Spotify client with dependency injection.

        Args:
            authenticator: Spotify authenticator instance

        Raises:
            SpotifyAuthError: If authentication fails
        """
        self._authenticator = authenticator
        self._sp: Optional[spotipy.Spotify] = None

    @property
    def sp(self) -> spotipy.Spotify:
        """
        Get authenticated Spotify client (lazy loading).

        Returns:
            Authenticated Spotify client
        """
        if self._sp is None:
            self._sp = self._authenticator.get_client()
        return self._sp

    @property
    def user_id(self) -> str:
        """
        Get current user ID.

        Returns:
            Spotify user ID
        """
        return self._authenticator.get_user_id()

    def user_playlist_create(
        self, user: str, name: str, public: bool = False, description: str = ""
    ) -> Dict:
        """
        Create a new playlist.

        Args:
            user: User ID
            name: Playlist name
            public: Whether playlist is public
            description: Playlist description

        Returns:
            Playlist information dictionary
        """
        logger.info(f"Creating playlist: {name}")
        return self.sp.user_playlist_create(
            user=user, name=name, public=public, description=description
        )

    def current_user_playlists(self, limit: int = 50, offset: int = 0) -> Dict:
        """
        Get current user's playlists.

        Args:
            limit: Maximum number of playlists to retrieve
            offset: Offset for pagination

        Returns:
            Dictionary containing playlists
        """
        return self.sp.current_user_playlists(limit=limit, offset=offset)

    def playlist_tracks(self, playlist_id: str) -> Dict:
        """
        Get tracks from a playlist.

        Args:
            playlist_id: Playlist ID

        Returns:
            Dictionary containing tracks
        """
        return self.sp.playlist_tracks(playlist_id)

    def next(self, result: Dict) -> Optional[Dict]:
        """
        Get next page of results.

        Args:
            result: Previous result dictionary

        Returns:
            Next page of results or None
        """
        return self.sp.next(result)

    def playlist_remove_all_occurrences_of_items(self, playlist_id: str, items: List[str]) -> Dict:
        """
        Remove all occurrences of tracks from playlist.

        Args:
            playlist_id: Playlist ID
            items: List of track URIs to remove

        Returns:
            Result dictionary
        """
        return self.sp.playlist_remove_all_occurrences_of_items(playlist_id, items)

    def playlist_change_details(
        self,
        playlist_id: str,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        collaborative: Optional[bool] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Change playlist details.

        Args:
            playlist_id: Playlist ID
            name: New playlist name
            public: Whether playlist is public
            collaborative: Whether playlist is collaborative
            description: New playlist description
        """
        self.sp.playlist_change_details(
            playlist_id=playlist_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        )

    def playlist_add_items(
        self, playlist_id: str, items: List[str], position: Optional[int] = None
    ) -> Dict:
        """
        Add tracks to a playlist.

        Args:
            playlist_id: Playlist ID
            items: List of track URIs to add
            position: Position to insert tracks (optional)

        Returns:
            Result dictionary
        """
        logger.debug(f"Adding {len(items)} items to playlist {playlist_id}")
        return self.sp.playlist_add_items(playlist_id, items, position)

    def track(self, track_id: str) -> Optional[Dict]:
        """
        Get track information by ID.

        Args:
            track_id: Spotify track ID

        Returns:
            Track information or None if not found
        """
        try:
            return self.sp.track(track_id=track_id)
        except Exception as e:
            logger.warning(f"Track {track_id} not found: {str(e)}")
            return None
