"""Tests for the refactored PlaylistManager."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spotichart.core.playlist_cache import PlaylistCache
from spotichart.core.playlist_manager import PlaylistManager
from spotichart.utils.exceptions import PlaylistCreationError


# Fixture to create a mock Spotify client
@pytest.fixture
def mock_spotify_client():
    """Provides a mock ISpotifyClient."""
    client = Mock()
    client.user_id = "user_123"
    # Mock ISpotifyClient methods
    client.user_playlist_create = Mock()
    client.current_user_playlists = Mock()
    client.playlist_tracks = Mock()
    client.next = Mock()
    client.playlist_remove_all_occurrences_of_items = Mock()
    client.playlist_change_details = Mock()
    return client


# Fixture for a temporary cache directory
@pytest.fixture
def temp_cache_dir(tmp_path):
    """Provides a temporary directory for cache testing."""
    cache_dir = tmp_path / ".spotichart" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class TestPlaylistManagerInit:
    """Tests for PlaylistManager initialization."""

    def test_init_with_client(self, mock_spotify_client, temp_cache_dir):
        with patch.object(Path, "home", return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_client)
            assert manager.client == mock_spotify_client

    def test_init_with_custom_cache(self, mock_spotify_client):
        cache = PlaylistCache(cache_file=None, ttl_hours=48)
        manager = PlaylistManager(mock_spotify_client, cache=cache)
        assert manager.cache == cache


class TestPlaylistManagerCache:
    """Tests for cache loading and saving."""

    def test_cache_integration(self, mock_spotify_client, temp_cache_dir):
        """Test that PlaylistManager integrates with PlaylistCache."""
        cache_file = temp_cache_dir / "playlists.json"
        playlist_data = {"id": "cached_123", "name": "Test Playlist"}
        cache_content = {
            "test playlist": {"playlist": playlist_data, "cached_at": datetime.now().isoformat()}
        }
        cache_file.write_text(json.dumps(cache_content))

        # Create manager with cache file
        cache = PlaylistCache(cache_file=cache_file, ttl_hours=24)
        manager = PlaylistManager(mock_spotify_client, cache=cache)

        # Should be able to get from cache
        cached = manager.cache.get("test playlist")
        assert cached is not None
        assert cached["id"] == "cached_123"


class TestPlaylistManagerCreate:
    """Tests for playlist creation."""

    def test_create_playlist_success(self, mock_spotify_client):
        created_playlist_data = {"id": "new_p_123", "name": "New Playlist"}
        mock_spotify_client.user_playlist_create.return_value = created_playlist_data

        cache = PlaylistCache(cache_file=None)
        manager = PlaylistManager(mock_spotify_client, cache=cache)
        playlist = manager.create("New Playlist", "A Description")

        assert playlist == created_playlist_data
        mock_spotify_client.user_playlist_create.assert_called_once()

    def test_create_failure_raises_exception(self, mock_spotify_client):
        mock_spotify_client.user_playlist_create.side_effect = Exception("API Error")

        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        with pytest.raises(PlaylistCreationError):
            manager.create("Test", "Desc")


class TestPlaylistManagerFindByName:
    """Tests for finding playlists."""

    def test_find_in_cache_first(self, mock_spotify_client):
        cached_playlist = {"id": "cached_123", "name": "Cached Playlist"}
        cache = PlaylistCache(cache_file=None)
        cache.set("cached playlist", cached_playlist)
        manager = PlaylistManager(mock_spotify_client, cache=cache)

        result = manager.find_by_name("Cached Playlist")
        assert result == cached_playlist
        mock_spotify_client.current_user_playlists.assert_not_called()

    def test_find_with_pagination(self, mock_spotify_client):
        """Should handle pagination correctly when searching for a playlist."""
        mock_spotify_client.current_user_playlists.side_effect = [
            {"items": [{"name": "Page 1 Playlist"}], "next": "page2"},
            {"items": [{"name": "Page 2 Playlist", "id": "p_found"}], "next": None},
        ]
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        result = manager.find_by_name("Page 2 Playlist")
        assert result["id"] == "p_found"
        assert mock_spotify_client.current_user_playlists.call_count == 2

    def test_find_not_found(self, mock_spotify_client):
        mock_spotify_client.current_user_playlists.return_value = {"items": [], "next": None}
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        result = manager.find_by_name("Nonexistent Playlist")
        assert result is None


class TestPlaylistManagerClear:
    """Tests for clearing playlists."""

    def test_clear_playlist_with_tracks(self, mock_spotify_client):
        mock_spotify_client.playlist_tracks.return_value = {
            "items": [{"track": {"uri": "uri_1"}}, {"track": {"uri": "uri_2"}}],
            "next": None,
        }
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        result = manager.clear("p_123")
        assert result is True
        mock_spotify_client.playlist_remove_all_occurrences_of_items.assert_called_once()

    def test_clear_failure_returns_false(self, mock_spotify_client):
        mock_spotify_client.playlist_tracks.side_effect = Exception("API Error")
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        result = manager.clear("p_123")
        assert result is False


class TestPlaylistManagerUpdateDetails:
    """Tests for updating playlist details."""

    def test_update_details_failure(self, mock_spotify_client):
        """Should return False if the API call fails."""
        mock_spotify_client.playlist_change_details.side_effect = Exception("API Error")
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        result = manager.update_details("p_123", "New Desc")
        assert result is False


class TestPlaylistManagerGetAll:
    """Tests for getting all playlists."""

    def test_get_all_success(self, mock_spotify_client):
        api_playlists = [{"id": "1", "name": "P1"}, {"id": "2", "name": "P2"}]
        mock_spotify_client.current_user_playlists.return_value = {"items": api_playlists}
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        playlists = manager.get_all(limit=2)
        assert playlists == api_playlists

    def test_get_all_failure_returns_empty_list(self, mock_spotify_client):
        mock_spotify_client.current_user_playlists.side_effect = Exception("API Error")
        manager = PlaylistManager(mock_spotify_client, cache=PlaylistCache(cache_file=None))
        playlists = manager.get_all()
        assert playlists == []
