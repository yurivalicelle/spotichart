"""Tests for the DependencyContainer."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from spotichart.core.dependency_container import DependencyContainer
from spotichart.core.spotify_authenticator import SpotifyAuthenticator
from spotichart.core.spotify_client import SpotifyClient
from spotichart.core.playlist_manager import PlaylistManager
from spotichart.core.track_manager import TrackManager
from spotichart.core.playlist_cache import PlaylistCache
from spotichart.core.spotify_service import SpotifyService
from spotichart.utils.configuration_provider import ConfigurationProvider


@pytest.fixture
def mock_config():
    """Provides a mock configuration provider."""
    config = Mock(spec=ConfigurationProvider)
    config.get.side_effect = lambda key, default=None: {
        'SPOTIFY_CLIENT_ID': 'test_client_id',
        'SPOTIFY_CLIENT_SECRET': 'test_client_secret',
        'REDIRECT_URI': 'http://localhost:8888/callback',
        'spotify.scope': 'playlist-modify-private playlist-modify-public',
        'settings.request_timeout': 30,
        'cache.enabled': True,
        'cache.ttl_hours': 24,
        'cache.playlist_cache_file': '.spotichart/cache/playlists.json'
    }.get(key, default)
    config.validate.return_value = True
    return config


class TestDependencyContainerInit:
    """Tests for DependencyContainer initialization."""

    def test_init_with_config(self, mock_config):
        """Should initialize with provided configuration."""
        container = DependencyContainer(config=mock_config)
        assert container.config == mock_config

    def test_init_without_config(self):
        """Should create default ConfigurationProvider if none provided."""
        with patch('spotichart.core.dependency_container.ConfigurationProvider') as mock_provider:
            container = DependencyContainer()
            mock_provider.assert_called_once()


class TestDependencyContainerGetters:
    """Tests for dependency getter methods."""

    @patch('spotichart.core.dependency_container.SpotifyAuthenticator')
    def test_get_authenticator_creates_instance(self, mock_auth_class, mock_config):
        """Should create SpotifyAuthenticator with correct configuration."""
        container = DependencyContainer(config=mock_config)

        authenticator = container.get_authenticator()

        mock_auth_class.assert_called_once()
        call_kwargs = mock_auth_class.call_args.kwargs
        assert call_kwargs['client_id'] == 'test_client_id'
        assert call_kwargs['client_secret'] == 'test_client_secret'
        assert call_kwargs['redirect_uri'] == 'http://localhost:8888/callback'

    @patch('spotichart.core.dependency_container.SpotifyAuthenticator')
    def test_get_authenticator_caches_instance(self, mock_auth_class, mock_config):
        """Should return same instance on subsequent calls (singleton)."""
        container = DependencyContainer(config=mock_config)

        auth1 = container.get_authenticator()
        auth2 = container.get_authenticator()

        assert mock_auth_class.call_count == 1
        assert auth1 == auth2

    @patch('spotichart.core.dependency_container.SpotifyClient')
    @patch('spotichart.core.dependency_container.SpotifyAuthenticator')
    def test_get_spotify_client_creates_with_authenticator(
        self, mock_auth_class, mock_client_class, mock_config
    ):
        """Should create SpotifyClient with authenticator dependency."""
        container = DependencyContainer(config=mock_config)

        client = container.get_spotify_client()

        mock_auth_class.assert_called_once()
        mock_client_class.assert_called_once_with(mock_auth_class.return_value)

    @patch('spotichart.core.dependency_container.PlaylistCache')
    def test_get_playlist_cache_creates_instance(self, mock_cache_class, mock_config):
        """Should create PlaylistCache with correct configuration."""
        container = DependencyContainer(config=mock_config)

        cache = container.get_playlist_cache()

        mock_cache_class.assert_called_once()
        call_kwargs = mock_cache_class.call_args.kwargs
        assert call_kwargs['ttl_hours'] == 24

    @patch('spotichart.core.dependency_container.PlaylistManager')
    @patch('spotichart.core.dependency_container.SpotifyClient')
    @patch('spotichart.core.dependency_container.PlaylistCache')
    def test_get_playlist_manager_injects_dependencies(
        self, mock_cache_class, mock_client_class, mock_manager_class, mock_config
    ):
        """Should create PlaylistManager with client and cache dependencies."""
        container = DependencyContainer(config=mock_config)

        manager = container.get_playlist_manager()

        mock_manager_class.assert_called_once()
        call_kwargs = mock_manager_class.call_args.kwargs
        assert 'client' in call_kwargs
        assert 'cache' in call_kwargs

    @patch('spotichart.core.dependency_container.TrackManager')
    @patch('spotichart.core.dependency_container.SpotifyClient')
    def test_get_track_manager_injects_client(
        self, mock_client_class, mock_manager_class, mock_config
    ):
        """Should create TrackManager with client dependency."""
        container = DependencyContainer(config=mock_config)

        manager = container.get_track_manager()

        mock_manager_class.assert_called_once()
        call_kwargs = mock_manager_class.call_args.kwargs
        assert 'client' in call_kwargs

    @patch('spotichart.core.dependency_container.SpotifyService')
    @patch('spotichart.core.dependency_container.PlaylistManager')
    @patch('spotichart.core.dependency_container.TrackManager')
    def test_get_spotify_service_injects_managers(
        self, mock_track_class, mock_playlist_class, mock_service_class, mock_config
    ):
        """Should create SpotifyService with playlist and track manager dependencies."""
        container = DependencyContainer(config=mock_config)

        service = container.get_spotify_service()

        mock_service_class.assert_called_once()
        call_kwargs = mock_service_class.call_args.kwargs
        assert 'playlists' in call_kwargs
        assert 'tracks' in call_kwargs


class TestDependencyContainerReset:
    """Tests for container reset functionality."""

    @patch('spotichart.core.dependency_container.SpotifyAuthenticator')
    def test_reset_clears_cached_instances(self, mock_auth_class, mock_config):
        """Should clear all cached instances on reset."""
        container = DependencyContainer(config=mock_config)

        # Create instance
        container.get_authenticator()
        assert mock_auth_class.call_count == 1

        # Reset
        container.reset()

        # Should create new instance
        container.get_authenticator()
        assert mock_auth_class.call_count == 2


class TestDependencyContainerValidation:
    """Tests for configuration validation."""

    def test_validate_configuration_calls_config_validate(self, mock_config):
        """Should delegate validation to config."""
        container = DependencyContainer(config=mock_config)

        result = container.validate_configuration()

        mock_config.validate.assert_called_once()
        assert result is True
