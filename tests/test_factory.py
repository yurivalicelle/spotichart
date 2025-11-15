"""Tests for the SpotifyServiceFactory with Dependency Injection."""

import pytest
from unittest.mock import patch, Mock
from spotichart.core.factory import SpotifyServiceFactory
from spotichart.core.spotify_service import SpotifyService
from spotichart.core.dependency_container import DependencyContainer


class TestSpotifyServiceFactory:
    """Tests for the refactored factory using DependencyContainer."""

    def setup_method(self):
        """Reset factory before each test."""
        SpotifyServiceFactory.reset()

    def teardown_method(self):
        """Clean up after each test."""
        SpotifyServiceFactory.reset()

    @patch('spotichart.core.factory.DependencyContainer')
    def test_create_returns_spotify_service(self, mock_container_class):
        """Should create and return SpotifyService through container."""
        # Setup mock
        mock_container = Mock(spec=DependencyContainer)
        mock_container.validate_configuration.return_value = True
        mock_service = Mock(spec=SpotifyService)
        mock_container.get_spotify_service.return_value = mock_service
        mock_container_class.return_value = mock_container

        # Call factory
        service = SpotifyServiceFactory.create()

        # Assertions
        mock_container_class.assert_called_once_with(config=None)
        mock_container.validate_configuration.assert_called_once()
        mock_container.get_spotify_service.assert_called_once()
        assert service == mock_service

    @patch('spotichart.core.factory.DependencyContainer')
    def test_create_with_custom_config(self, mock_container_class):
        """Should accept and use custom configuration."""
        # Setup
        custom_config = Mock()
        mock_container = Mock(spec=DependencyContainer)
        mock_container.validate_configuration.return_value = True
        mock_service = Mock(spec=SpotifyService)
        mock_container.get_spotify_service.return_value = mock_service
        mock_container_class.return_value = mock_container

        # Call with custom config
        service = SpotifyServiceFactory.create(config=custom_config)

        # Should pass custom config to container
        mock_container_class.assert_called_once_with(config=custom_config)
        assert service == mock_service

    @patch('spotichart.core.factory.DependencyContainer')
    def test_create_validates_configuration(self, mock_container_class):
        """Should validate configuration before creating service."""
        # Setup invalid configuration
        mock_container = Mock(spec=DependencyContainer)
        mock_container.validate_configuration.return_value = False
        mock_container_class.return_value = mock_container

        # Should raise ValueError on invalid config
        with pytest.raises(ValueError, match="Invalid configuration"):
            SpotifyServiceFactory.create()

        mock_container.validate_configuration.assert_called_once()
        mock_container.get_spotify_service.assert_not_called()

    @patch('spotichart.core.factory.DependencyContainer')
    def test_get_container_returns_container(self, mock_container_class):
        """Should provide access to the dependency container."""
        mock_container = Mock(spec=DependencyContainer)
        mock_container_class.return_value = mock_container

        container = SpotifyServiceFactory.get_container()

        assert container == mock_container
        mock_container_class.assert_called_once()

    @patch('spotichart.core.factory.DependencyContainer')
    def test_reset_clears_cached_container(self, mock_container_class):
        """Should reset cached container and all dependencies."""
        # Create container
        mock_container = Mock(spec=DependencyContainer)
        mock_container_class.return_value = mock_container

        SpotifyServiceFactory.get_container()
        assert mock_container_class.call_count == 1

        # Reset
        SpotifyServiceFactory.reset()

        # Should call reset on container
        mock_container.reset.assert_called_once()

        # Next call should create new container
        SpotifyServiceFactory.get_container()
        assert mock_container_class.call_count == 2

    @patch('spotichart.core.factory.DependencyContainer')
    def test_container_caching(self, mock_container_class):
        """Should cache and reuse container instance."""
        mock_container = Mock(spec=DependencyContainer)
        mock_container.validate_configuration.return_value = True
        mock_service1 = Mock(spec=SpotifyService)
        mock_service2 = Mock(spec=SpotifyService)
        mock_container.get_spotify_service.side_effect = [mock_service1, mock_service2]
        mock_container_class.return_value = mock_container

        # Create service twice
        service1 = SpotifyServiceFactory.create()
        service2 = SpotifyServiceFactory.create()

        # Should only create container once
        assert mock_container_class.call_count == 1
        # But may create different services
        assert mock_container.get_spotify_service.call_count == 2
