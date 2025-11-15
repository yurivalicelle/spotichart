"""Tests for core interfaces."""

import pytest
from abc import ABC
from spotichart.core.interfaces import (
    IConfiguration,
    ISpotifyAuth,
    IPlaylistOperations,
    ITrackOperations
)


class TestIConfiguration:
    """Test IConfiguration interface contract."""

    def test_is_abstract(self):
        """IConfiguration should be abstract."""
        assert issubclass(IConfiguration, ABC)

    def test_cannot_instantiate_directly(self):
        """Cannot instantiate IConfiguration directly."""
        with pytest.raises(TypeError):
            IConfiguration()

    def test_has_required_methods(self):
        """IConfiguration has required abstract methods."""
        assert hasattr(IConfiguration, 'get')
        assert hasattr(IConfiguration, 'validate')

    def test_mock_implementation(self, mock_config_interface):
        """Mock implementation satisfies interface."""
        assert isinstance(mock_config_interface, object)
        assert hasattr(mock_config_interface, 'get')
        assert hasattr(mock_config_interface, 'validate')

        # Test get method
        value = mock_config_interface.get('client_id')
        assert value == 'test_client_id'

        # Test validate method
        assert mock_config_interface.validate() is True


class TestISpotifyAuth:
    """Test ISpotifyAuth interface contract."""

    def test_is_abstract(self):
        """ISpotifyAuth should be abstract."""
        assert issubclass(ISpotifyAuth, ABC)

    def test_cannot_instantiate_directly(self):
        """Cannot instantiate ISpotifyAuth directly."""
        with pytest.raises(TypeError):
            ISpotifyAuth()

    def test_has_required_methods(self):
        """ISpotifyAuth has required abstract methods."""
        assert hasattr(ISpotifyAuth, 'get_client')
        assert hasattr(ISpotifyAuth, 'get_user_id')

    def test_mock_implementation(self, mock_spotify_auth):
        """Mock implementation satisfies interface."""
        assert hasattr(mock_spotify_auth, 'get_client')
        assert hasattr(mock_spotify_auth, 'get_user_id')

        # Test methods
        client = mock_spotify_auth.get_client()
        assert client is not None

        user_id = mock_spotify_auth.get_user_id()
        assert user_id == 'test_user_123'


class TestIPlaylistOperations:
    """Test IPlaylistOperations interface contract."""

    def test_is_abstract(self):
        """IPlaylistOperations should be abstract."""
        assert issubclass(IPlaylistOperations, ABC)

    def test_cannot_instantiate_directly(self):
        """Cannot instantiate IPlaylistOperations directly."""
        with pytest.raises(TypeError):
            IPlaylistOperations()

    def test_has_required_methods(self):
        """IPlaylistOperations has required abstract methods."""
        assert hasattr(IPlaylistOperations, 'create')
        assert hasattr(IPlaylistOperations, 'find_by_name')
        assert hasattr(IPlaylistOperations, 'clear')
        assert hasattr(IPlaylistOperations, 'update_details')
        assert hasattr(IPlaylistOperations, 'get_all')

    def test_mock_implementation(self, mock_playlist_operations):
        """Mock implementation satisfies interface."""
        # Test create
        playlist = mock_playlist_operations.create('Test', 'Description')
        assert playlist['id'] == 'playlist_123'

        # Test find_by_name
        found = mock_playlist_operations.find_by_name('Test')
        assert found is None  # Default mock behavior

        # Test clear
        result = mock_playlist_operations.clear('playlist_123')
        assert result is True

        # Test update_details
        result = mock_playlist_operations.update_details('playlist_123', 'New desc')
        assert result is True

        # Test get_all
        playlists = mock_playlist_operations.get_all()
        assert isinstance(playlists, list)


class TestITrackOperations:
    """Test ITrackOperations interface contract."""

    def test_is_abstract(self):
        """ITrackOperations should be abstract."""
        assert issubclass(ITrackOperations, ABC)

    def test_cannot_instantiate_directly(self):
        """Cannot instantiate ITrackOperations directly."""
        with pytest.raises(TypeError):
            ITrackOperations()

    def test_has_required_methods(self):
        """ITrackOperations has required abstract methods."""
        assert hasattr(ITrackOperations, 'add_to_playlist')
        assert hasattr(ITrackOperations, 'search')
        assert hasattr(ITrackOperations, 'build_uri')

    def test_mock_implementation(self, mock_track_operations):
        """Mock implementation satisfies interface."""
        # Test add_to_playlist
        count = mock_track_operations.add_to_playlist('playlist_123', ['track1', 'track2'])
        assert count == 10

        # Test search
        track = mock_track_operations.search('track_123')
        assert track['id'] == 'track_123'

        # Test build_uri
        uri = mock_track_operations.build_uri('track_123')
        assert uri == 'spotify:track:track_123'


class TestInterfaceSegregation:
    """Test that interfaces follow Interface Segregation Principle."""

    def test_interfaces_are_focused(self):
        """Each interface should have a focused responsibility."""
        # IConfiguration - only config methods
        config_methods = [m for m in dir(IConfiguration) if not m.startswith('_')]
        assert len([m for m in config_methods if not m.startswith('__')]) <= 3

        # ISpotifyAuth - only auth methods
        auth_methods = [m for m in dir(ISpotifyAuth) if not m.startswith('_')]
        assert len([m for m in auth_methods if not m.startswith('__')]) <= 3

        # IPlaylistOperations - only playlist methods
        playlist_methods = [m for m in dir(IPlaylistOperations) if not m.startswith('_')]
        assert len([m for m in playlist_methods if not m.startswith('__')]) <= 6

        # ITrackOperations - only track methods
        track_methods = [m for m in dir(ITrackOperations) if not m.startswith('_')]
        assert len([m for m in track_methods if not m.startswith('__')]) <= 4

    def test_no_interface_depends_on_another(self):
        """Interfaces should be independent (no inheritance between them)."""
        # IConfiguration doesn't inherit from others
        assert ISpotifyAuth not in IConfiguration.__bases__
        assert IPlaylistOperations not in IConfiguration.__bases__
        assert ITrackOperations not in IConfiguration.__bases__

        # ISpotifyAuth doesn't inherit from others
        assert IConfiguration not in ISpotifyAuth.__bases__
        assert IPlaylistOperations not in ISpotifyAuth.__bases__
        assert ITrackOperations not in ISpotifyAuth.__bases__
