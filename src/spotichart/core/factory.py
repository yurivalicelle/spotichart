"""
Spotify Service Factory Module

Provides simplified factory interface using DependencyContainer.
Follows SOLID principles with dependency injection.
"""

import logging
from typing import Optional

from ..utils.interfaces import IConfiguration
from .dependency_container import DependencyContainer
from .spotify_service import SpotifyService

logger = logging.getLogger(__name__)


class SpotifyServiceFactory:
    """
    Factory for creating SpotifyService instances.
    Now delegates to DependencyContainer for proper dependency injection.
    """

    _container: Optional[DependencyContainer] = None

    @classmethod
    def create(cls, config: Optional[IConfiguration] = None) -> SpotifyService:
        """
        Create SpotifyService with all dependencies properly injected.

        Args:
            config: Optional configuration provider.
                   If None, uses default ConfigurationProvider.

        Returns:
            Fully configured SpotifyService instance

        Example:
            >>> service = SpotifyServiceFactory.create()
            >>> # Or with custom config:
            >>> custom_config = ConfigurationProvider(Path('custom_config.yaml'))
            >>> service = SpotifyServiceFactory.create(config=custom_config)
        """
        logger.info("Creating SpotifyService via Factory")

        # Create or reuse container
        if cls._container is None or config is not None:
            cls._container = DependencyContainer(config=config)

        # Validate configuration
        if not cls._container.validate_configuration():
            raise ValueError("Invalid configuration. Please check your .env file and config.yaml")

        # Get service from container
        return cls._container.get_spotify_service()

    @classmethod
    def get_container(cls) -> DependencyContainer:
        """
        Get the dependency container instance.

        Useful for accessing individual dependencies or testing.

        Returns:
            DependencyContainer instance

        Example:
            >>> container = SpotifyServiceFactory.get_container()
            >>> playlist_manager = container.get_playlist_manager()
            >>> track_manager = container.get_track_manager()
        """
        if cls._container is None:
            cls._container = DependencyContainer()
        return cls._container

    @classmethod
    def reset(cls) -> None:
        """
        Reset factory state.

        Clears cached container and all dependencies.
        Useful for testing or reconfiguration.
        """
        logger.info("Resetting SpotifyServiceFactory")
        if cls._container is not None:
            cls._container.reset()
        cls._container = None
