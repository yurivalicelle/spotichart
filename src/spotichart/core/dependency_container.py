"""
Dependency Container Module

Manages dependency injection following Dependency Inversion Principle.
Centralizes object creation and wiring.
"""

import logging
from pathlib import Path
from typing import Optional

from ..utils.configuration_provider import ConfigurationProvider
from ..utils.interfaces import IConfiguration
from .interfaces import IPlaylistOperations, ISpotifyClient, ITrackOperations
from .playlist_cache import PlaylistCache
from .playlist_manager import PlaylistManager
from .spotify_authenticator import SpotifyAuthenticator
from .spotify_client import SpotifyClient
from .spotify_service import SpotifyService
from .track_manager import TrackManager

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency Injection Container.

    Manages the creation and lifetime of application dependencies.
    Follows SOLID principles by depending on abstractions.
    """

    def __init__(self, config: Optional[IConfiguration] = None):
        """
        Initialize dependency container.

        Args:
            config: Configuration provider (if None, creates default ConfigurationProvider)
        """
        # Configuration
        self._config = config or ConfigurationProvider()

        # Core dependencies (lazy-loaded)
        self._authenticator: Optional[SpotifyAuthenticator] = None
        self._spotify_client: Optional[ISpotifyClient] = None
        self._playlist_cache: Optional[PlaylistCache] = None
        self._playlist_manager: Optional[IPlaylistOperations] = None
        self._track_manager: Optional[ITrackOperations] = None
        self._spotify_service: Optional[SpotifyService] = None

    @property
    def config(self) -> IConfiguration:
        """Get configuration instance."""
        return self._config

    def get_authenticator(self) -> SpotifyAuthenticator:
        """
        Get or create SpotifyAuthenticator instance.

        Returns:
            SpotifyAuthenticator instance
        """
        if self._authenticator is None:
            logger.info("Creating SpotifyAuthenticator")

            # Get configuration values
            client_id = self._config.get("SPOTIFY_CLIENT_ID")
            client_secret = self._config.get("SPOTIFY_CLIENT_SECRET")
            redirect_uri = self._config.get("REDIRECT_URI", "http://localhost:8888/callback")
            scope = self._config.get(
                "spotify.scope", "playlist-modify-private playlist-modify-public"
            )
            request_timeout = self._config.get("settings.request_timeout", 30)

            # Create cache directory
            cache_dir = Path.home() / ".spotichart" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = cache_dir / "spotify_token.cache"

            self._authenticator = SpotifyAuthenticator(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=cache_path,
                request_timeout=request_timeout,
            )

        return self._authenticator

    def get_spotify_client(self) -> ISpotifyClient:
        """
        Get or create SpotifyClient instance.

        Returns:
            ISpotifyClient instance
        """
        if self._spotify_client is None:
            logger.info("Creating SpotifyClient")
            authenticator = self.get_authenticator()
            self._spotify_client = SpotifyClient(authenticator)

        return self._spotify_client

    def get_playlist_cache(self) -> PlaylistCache:
        """
        Get or create PlaylistCache instance.

        Returns:
            PlaylistCache instance
        """
        if self._playlist_cache is None:
            logger.info("Creating PlaylistCache")

            cache_enabled = self._config.get("cache.enabled", True)
            cache_ttl_hours = self._config.get("cache.ttl_hours", 24)

            if cache_enabled:
                cache_file_str = self._config.get(
                    "cache.playlist_cache_file", ".spotichart/cache/playlists.json"
                )
                cache_file = Path.home() / cache_file_str
                self._playlist_cache = PlaylistCache(
                    cache_file=cache_file, ttl_hours=cache_ttl_hours
                )
            else:
                # In-memory cache only
                self._playlist_cache = PlaylistCache(cache_file=None, ttl_hours=cache_ttl_hours)

        return self._playlist_cache

    def get_playlist_manager(self) -> IPlaylistOperations:
        """
        Get or create PlaylistManager instance.

        Returns:
            IPlaylistOperations instance
        """
        if self._playlist_manager is None:
            logger.info("Creating PlaylistManager")
            client = self.get_spotify_client()
            cache = self.get_playlist_cache()
            self._playlist_manager = PlaylistManager(client=client, cache=cache)

        return self._playlist_manager

    def get_track_manager(self) -> ITrackOperations:
        """
        Get or create TrackManager instance.

        Returns:
            ITrackOperations instance
        """
        if self._track_manager is None:
            logger.info("Creating TrackManager")
            client = self.get_spotify_client()
            self._track_manager = TrackManager(client=client)

        return self._track_manager

    def get_spotify_service(self) -> SpotifyService:
        """
        Get or create SpotifyService instance with all dependencies.

        Returns:
            SpotifyService instance with segregated interfaces injected
        """
        if self._spotify_service is None:
            logger.info("Creating SpotifyService with segregated interfaces")

            # Get legacy dependencies
            playlists = self.get_playlist_manager()
            tracks = self.get_track_manager()

            # Get client (implements all segregated interfaces)
            client = self.get_spotify_client()

            # Inject both legacy and new segregated interfaces
            # The client implements IPlaylistReader, IPlaylistWriter, ITrackWriter
            self._spotify_service = SpotifyService(
                playlists=playlists,
                tracks=tracks,
                playlist_reader=client,  # Segregated interface
                playlist_writer=client,  # Segregated interface
                track_writer=client,  # Segregated interface
            )

        return self._spotify_service

    def validate_configuration(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        return self._config.validate()

    def reset(self) -> None:
        """
        Reset all cached instances.
        Useful for testing or reconfiguration.
        """
        logger.info("Resetting dependency container")
        self._authenticator = None
        self._spotify_client = None
        self._playlist_cache = None
        self._playlist_manager = None
        self._track_manager = None
        self._spotify_service = None
