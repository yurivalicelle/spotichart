"""
Spotify Authenticator Module

Handles Spotify API authentication following Single Responsibility Principle.
"""

import logging
from typing import Optional
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ..utils.exceptions import SpotifyAuthError

logger = logging.getLogger(__name__)


class SpotifyAuthenticator:
    """Handles Spotify OAuth authentication."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scope: str,
        cache_path: Optional[Path] = None,
        request_timeout: int = 30,
    ):
        """
        Initialize Spotify authenticator.

        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret
            redirect_uri: OAuth redirect URI
            scope: Spotify API scopes
            cache_path: Path to token cache file
            request_timeout: Request timeout in seconds

        Raises:
            SpotifyAuthError: If authentication fails
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.cache_path = cache_path
        self.request_timeout = request_timeout

        self._sp: Optional[spotipy.Spotify] = None
        self._user_id: Optional[str] = None

    def authenticate(self) -> spotipy.Spotify:
        """
        Authenticate with Spotify API.

        Returns:
            Authenticated Spotify client

        Raises:
            SpotifyAuthError: If authentication fails
        """
        if self._sp is not None:
            return self._sp

        try:
            logger.info("Authenticating with Spotify API")

            cache_path_str = str(self.cache_path) if self.cache_path else None

            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                show_dialog=True,
                requests_timeout=self.request_timeout,
                cache_path=cache_path_str,
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)

            # Verify authentication by getting user info
            user_info = self._sp.me()
            self._user_id = user_info["id"]
            logger.info(f"Successfully authenticated as user: {self._user_id}")

            return self._sp

        except Exception as e:
            logger.error(f"Failed to authenticate with Spotify: {str(e)}")
            raise SpotifyAuthError(f"Authentication failed: {str(e)}") from e

    def get_client(self) -> spotipy.Spotify:
        """
        Get authenticated Spotify client (lazy loading).

        Returns:
            Authenticated Spotify client

        Raises:
            SpotifyAuthError: If authentication fails
        """
        if self._sp is None:
            return self.authenticate()
        return self._sp

    def get_user_id(self) -> str:
        """
        Get current user ID.

        Returns:
            Spotify user ID

        Raises:
            SpotifyAuthError: If not authenticated
        """
        if self._user_id is None:
            # Trigger authentication if not done yet
            self.authenticate()
        return self._user_id
