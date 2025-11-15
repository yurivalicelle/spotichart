"""
Spotify Client Module

Handles all Spotify API interactions.
"""

import logging
from typing import List, Dict, Optional
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ..config import Config
from ..utils.exceptions import SpotifyAuthError, PlaylistCreationError

logger = logging.getLogger(__name__)


class SpotifyClient:
    """Wrapper class for Spotify API interactions."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scope: Optional[str] = None
    ):
        """
        Initialize Spotify client.

        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret
            redirect_uri: OAuth redirect URI
            scope: Spotify API scopes

        Raises:
            SpotifyAuthError: If authentication fails
        """
        self.client_id = client_id or Config.SPOTIFY_CLIENT_ID
        self.client_secret = client_secret or Config.SPOTIFY_CLIENT_SECRET
        self.redirect_uri = redirect_uri or Config.REDIRECT_URI
        self.scope = scope or Config.SPOTIFY_SCOPE

        self._sp: Optional[spotipy.Spotify] = None
        self._user_id: Optional[str] = None
        self._playlist_cache: Dict[str, Dict] = {}  # Cache for recently created playlists

    @property
    def sp(self) -> spotipy.Spotify:
        """
        Get authenticated Spotify client (lazy loading).

        Returns:
            Authenticated Spotify client

        Raises:
            SpotifyAuthError: If authentication fails
        """
        if self._sp is None:
            self._authenticate()
        return self._sp

    def _authenticate(self) -> None:
        """
        Authenticate with Spotify API.

        Raises:
            SpotifyAuthError: If authentication fails
        """
        try:
            logger.info("Authenticating with Spotify API")

            # Use a specific cache file path instead of directory
            cache_path = str(Config.CACHE_DIR / 'spotify_token.cache')

            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                show_dialog=True,
                requests_timeout=Config.REQUEST_TIMEOUT,
                cache_path=cache_path
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)

            # Verify authentication by getting user info
            user_info = self._sp.me()
            self._user_id = user_info['id']
            logger.info(f"Successfully authenticated as user: {self._user_id}")

        except Exception as e:
            logger.error(f"Failed to authenticate with Spotify: {str(e)}")
            raise SpotifyAuthError(f"Authentication failed: {str(e)}") from e

    @property
    def user_id(self) -> str:
        """
        Get current user ID.

        Returns:
            Spotify user ID
        """
        if self._user_id is None:
            # Trigger authentication if not done yet
            _ = self.sp
        return self._user_id

    def create_playlist(
        self,
        name: str,
        description: str = '',
        public: bool = False
    ) -> Dict:
        """
        Create a new Spotify playlist.

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
            playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=name,
                public=public,
                description=description
            )
            logger.info(f"Playlist created successfully: {playlist['id']}")

            # Add to local cache (Spotify API may have delay showing new playlists)
            cache_key = name.lower().strip()
            self._playlist_cache[cache_key] = playlist
            logger.debug(f"Added playlist to local cache: {cache_key}")

            return playlist
        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise PlaylistCreationError(f"Playlist creation failed: {str(e)}") from e

    def search_track(self, track_id: str) -> Optional[Dict]:
        """
        Search for a track by ID.

        Args:
            track_id: Spotify track ID

        Returns:
            Track information or None if not found
        """
        try:
            result = self.sp.track(track_id=track_id)
            return result
        except Exception as e:
            logger.warning(f"Track {track_id} not found: {str(e)}")
            return None

    def add_tracks_to_playlist(
        self,
        playlist_id: str,
        track_uris: List[str],
        batch_size: Optional[int] = None
    ) -> int:
        """
        Add tracks to a playlist in batches.

        Args:
            playlist_id: Playlist ID
            track_uris: List of track URIs
            batch_size: Number of tracks per batch (default: Config.SPOTIFY_BATCH_SIZE)

        Returns:
            Number of tracks successfully added

        Raises:
            PlaylistCreationError: If adding tracks fails
        """
        if batch_size is None:
            batch_size = Config.SPOTIFY_BATCH_SIZE

        added_count = 0
        total_batches = (len(track_uris) + batch_size - 1) // batch_size

        try:
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                batch_num = i // batch_size + 1

                logger.info(f"Adding batch {batch_num}/{total_batches}: {len(batch)} tracks")

                self.sp.playlist_add_items(playlist_id, batch)
                added_count += len(batch)

                # Add small delay to avoid rate limiting
                if batch_num < total_batches:
                    time.sleep(0.5)

            logger.info(f"Successfully added {added_count} tracks to playlist")
            return added_count

        except Exception as e:
            logger.error(f"Failed to add tracks to playlist: {str(e)}")
            raise PlaylistCreationError(f"Adding tracks failed: {str(e)}") from e

    def create_playlist_with_tracks(
        self,
        name: str,
        track_ids: List[str],
        description: str = '',
        public: bool = False
    ) -> tuple[str, int, List[str]]:
        """
        Create a playlist and add tracks to it.

        Args:
            name: Playlist name
            track_ids: List of track IDs
            description: Playlist description
            public: Whether playlist is public

        Returns:
            Tuple of (playlist URL, number of tracks added, list of failed track IDs)
        """
        # Create playlist
        playlist = self.create_playlist(name, description, public)
        playlist_id = playlist['id']

        # Convert track IDs to URIs directly (much faster)
        track_uris = []

        logger.info(f"Processing {len(track_ids)} tracks")

        for track_id in track_ids:
            if track_id and track_id.strip():
                # Build URI directly - Spotify API will ignore invalid ones
                track_uris.append(f"spotify:track:{track_id.strip()}")

        # Add tracks to playlist
        failed_tracks = []
        if track_uris:
            try:
                self.add_tracks_to_playlist(playlist_id, track_uris)
            except Exception as e:
                logger.warning(f"Some tracks may have failed to add: {str(e)}")
                # Note: Spotify API doesn't provide easy way to know which specific tracks failed
                # when adding in batch, so we can't populate failed_tracks accurately

        playlist_url = playlist['external_urls']['spotify']

        logger.info(
            f"Playlist created: {len(track_uris)} track URIs sent to Spotify"
        )

        return playlist_url, len(track_uris), failed_tracks

    def get_user_playlists(self, limit: int = 50) -> List[Dict]:
        """
        Get user's playlists.

        Args:
            limit: Maximum number of playlists to retrieve

        Returns:
            List of playlist dictionaries
        """
        try:
            playlists = self.sp.current_user_playlists(limit=limit)
            return playlists['items']
        except Exception as e:
            logger.error(f"Failed to get user playlists: {str(e)}")
            return []

    def find_playlist_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a playlist by name in user's library.

        Args:
            name: Playlist name to search for

        Returns:
            Playlist dictionary if found, None otherwise
        """
        try:
            logger.info(f"Searching for playlist: '{name}'")

            # Check cache first (recently created playlists might not appear in API)
            cache_key = name.lower().strip()
            if cache_key in self._playlist_cache:
                logger.info(f"✓ Found playlist in cache: {self._playlist_cache[cache_key]['id']}")
                return self._playlist_cache[cache_key]

            # Get all user playlists (paginated)
            offset = 0
            limit = 50
            checked_count = 0

            while True:
                playlists = self.sp.current_user_playlists(limit=limit, offset=offset)

                for playlist in playlists['items']:
                    checked_count += 1
                    playlist_name = playlist['name']
                    logger.debug(f"Checking playlist #{checked_count}: '{playlist_name}'")

                    if playlist_name.lower().strip() == name.lower().strip():
                        logger.info(f"✓ Found existing playlist: {playlist['id']} - '{playlist_name}'")
                        # Add to cache for future lookups
                        self._playlist_cache[cache_key] = playlist
                        return playlist

                # Check if there are more playlists
                if playlists['next'] is None:
                    break

                offset += limit

            logger.info(f"✗ Playlist '{name}' not found after checking {checked_count} playlists")
            return None

        except Exception as e:
            logger.error(f"Error searching for playlist: {str(e)}")
            return None

    def clear_playlist(self, playlist_id: str) -> bool:
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
            results = self.sp.playlist_tracks(playlist_id)
            tracks.extend(results['items'])

            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            # Remove in batches of 100
            track_uris = [item['track']['uri'] for item in tracks if item['track']]

            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i + 100]
                self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
                logger.debug(f"Removed batch {i//100 + 1}")

            logger.info(f"Cleared {len(track_uris)} tracks from playlist")
            return True

        except Exception as e:
            logger.error(f"Failed to clear playlist: {str(e)}")
            return False

    def update_playlist(
        self,
        playlist_id: str,
        track_ids: List[str],
        replace: bool = True
    ) -> tuple[int, List[str]]:
        """
        Update an existing playlist with new tracks.

        Args:
            playlist_id: Playlist ID to update
            track_ids: List of track IDs to add
            replace: If True, replace all tracks. If False, append.

        Returns:
            Tuple of (number of tracks added, list of failed track IDs)
        """
        try:
            logger.info(f"Updating playlist: {playlist_id} (replace={replace})")

            # Clear playlist if replace mode
            if replace:
                self.clear_playlist(playlist_id)

            # Convert track IDs to URIs directly (much faster)
            track_uris = []

            for track_id in track_ids:
                if track_id and track_id.strip():
                    # Build URI directly - Spotify API will ignore invalid ones
                    track_uris.append(f"spotify:track:{track_id.strip()}")

            # Add tracks in batches
            failed_tracks = []
            if track_uris:
                try:
                    self.add_tracks_to_playlist(playlist_id, track_uris)
                except Exception as e:
                    logger.warning(f"Some tracks may have failed to add: {str(e)}")

            mode = "replaced with" if replace else "appended"
            logger.info(f"Playlist {mode} {len(track_uris)} track URIs")

            return len(track_uris), failed_tracks

        except Exception as e:
            logger.error(f"Failed to update playlist: {str(e)}")
            raise PlaylistCreationError(f"Update failed: {str(e)}") from e

    def create_or_update_playlist(
        self,
        name: str,
        track_ids: List[str],
        description: str = '',
        public: bool = False,
        update_mode: str = 'replace'
    ) -> tuple[str, int, List[str], bool]:
        """
        Intelligently create or update a playlist.

        Checks if playlist exists:
        - If exists: updates it
        - If not exists: creates new one

        Args:
            name: Playlist name
            track_ids: List of track IDs
            description: Playlist description
            public: Whether playlist is public
            update_mode: 'replace' to replace tracks, 'append' to add to existing

        Returns:
            Tuple of (playlist URL, tracks added, failed tracks, was_updated)
        """
        try:
            # Search for existing playlist
            existing = self.find_playlist_by_name(name)

            if existing:
                # Update existing playlist
                logger.info(f"Playlist '{name}' exists, updating...")

                playlist_id = existing['id']
                playlist_url = existing['external_urls']['spotify']

                # Update tracks
                replace = (update_mode == 'replace')
                added_count, failed = self.update_playlist(
                    playlist_id,
                    track_ids,
                    replace=replace
                )

                # Update description if provided
                if description:
                    try:
                        self.sp.playlist_change_details(
                            playlist_id,
                            description=description
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update description: {str(e)}")

                return playlist_url, added_count, failed, True

            else:
                # Create new playlist
                logger.info(f"Playlist '{name}' not found, creating new...")

                url, count, failed = self.create_playlist_with_tracks(
                    name=name,
                    track_ids=track_ids,
                    description=description,
                    public=public
                )

                return url, count, failed, False

        except Exception as e:
            logger.error(f"Failed to create or update playlist: {str(e)}")
            raise PlaylistCreationError(f"Operation failed: {str(e)}") from e
