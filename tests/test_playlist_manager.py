"""Tests for PlaylistManager."""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from spotichart.core.playlist_manager import PlaylistManager
from spotichart.utils.exceptions import PlaylistCreationError


class TestPlaylistManagerInit:
    """Test PlaylistManager initialization."""

    def test_init_with_auth(self, mock_spotify_auth, temp_cache_dir):
        """Initialize PlaylistManager with auth interface."""
        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            assert manager.auth == mock_spotify_auth
            assert manager.cache_ttl == timedelta(hours=24)
            assert isinstance(manager._playlist_cache, dict)

    def test_init_with_custom_ttl(self, mock_spotify_auth, temp_cache_dir):
        """Initialize with custom cache TTL."""
        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth, cache_ttl_hours=48)

            assert manager.cache_ttl == timedelta(hours=48)

    def test_cache_file_location(self, mock_spotify_auth, temp_cache_dir):
        """Cache file is in correct location."""
        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            expected_path = temp_cache_dir.parent.parent / '.spotichart' / 'cache' / 'playlists.json'
            assert manager.cache_file == expected_path


class TestPlaylistManagerCache:
    """Test PlaylistManager persistent cache functionality."""

    def test_load_cache_empty_file(self, mock_spotify_auth, temp_cache_dir):
        """Load cache when file doesn't exist."""
        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            assert len(manager._playlist_cache) == 0

    def test_load_cache_with_valid_data(self, mock_spotify_auth, temp_cache_dir):
        """Load cache with valid data."""
        cache_file = temp_cache_dir / 'playlists.json'
        cache_data = {
            'test playlist': {
                'playlist': {
                    'id': 'cached_123',
                    'name': 'Test Playlist'
                },
                'cached_at': datetime.now().isoformat()
            }
        }

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)
            # Override the instance attribute for testing
            manager.cache_file = cache_file
            manager._playlist_cache = manager._load_cache() # Reload cache

            assert 'test playlist' in manager._playlist_cache
            assert manager._playlist_cache['test playlist']['id'] == 'cached_123'

    def test_load_cache_expires_old_entries(self, mock_spotify_auth, temp_cache_dir):
        """Expired cache entries are not loaded."""
        cache_file = temp_cache_dir / 'playlists.json'
        old_time = (datetime.now() - timedelta(hours=48)).isoformat()
        cache_data = {
            'old playlist': {
                'playlist': {'id': 'old_123', 'name': 'Old'},
                'cached_at': old_time
            }
        }

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth, cache_ttl_hours=24)
            manager.cache_file = cache_file
            manager._playlist_cache = manager._load_cache()

            assert 'old playlist' not in manager._playlist_cache

    def test_save_cache(self, mock_spotify_auth, temp_cache_dir):
        """Save cache to file."""
        cache_file = temp_cache_dir / 'playlists.json'

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)
            manager.cache_file = cache_file
            manager._playlist_cache['new playlist'] = {
                'id': 'new_123',
                'name': 'New Playlist'
            }

            manager._save_cache()

            assert cache_file.exists()
            with open(cache_file, 'r') as f:
                saved_data = json.load(f)

            assert 'new playlist' in saved_data
            assert saved_data['new playlist']['playlist']['id'] == 'new_123'
            assert 'cached_at' in saved_data['new playlist']


class TestPlaylistManagerCreate:
    """Test playlist creation."""

    def test_create_playlist_success(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Create playlist successfully."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_auth.get_user_id.return_value = 'user_123'

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            playlist = manager.create('Test Playlist', 'Description', public=False)

            assert playlist['id'] == 'playlist_123'
            assert playlist['name'] == 'Test Playlist'
            mock_spotify_client.user_playlist_create.assert_called_once_with(
                user='user_123',
                name='Test Playlist',
                public=False,
                description='Description'
            )

    def test_create_adds_to_cache(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Creating playlist adds it to cache."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_auth.get_user_id.return_value = 'user_123'

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            manager.create('Test Playlist', 'Description')

            cache_key = 'test playlist'
            assert cache_key in manager._playlist_cache
            assert manager._playlist_cache[cache_key]['id'] == 'playlist_123'

    def test_create_saves_cache_to_file(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Creating playlist saves cache to file."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_auth.get_user_id.return_value = 'user_123'

        cache_file = temp_cache_dir / 'playlists.json'

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)
            manager.cache_file = cache_file
            manager.create('Test Playlist', 'Description')

            assert cache_file.exists()

    def test_create_failure_raises_exception(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Failed playlist creation raises PlaylistCreationError."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.user_playlist_create.side_effect = Exception('API Error')

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            with pytest.raises(PlaylistCreationError) as exc_info:
                manager.create('Test', 'Desc')

            assert 'Playlist creation failed' in str(exc_info.value)


class TestPlaylistManagerFindByName:
    """Test finding playlists by name."""

    def test_find_in_cache(self, mock_spotify_auth, temp_cache_dir):
        """Find playlist in cache (doesn't hit API)."""
        mock_spotify_client = Mock()

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)
            manager._playlist_cache['test playlist'] = {
                'id': 'cached_123',
                'name': 'Test Playlist'
            }

            result = manager.find_by_name('Test Playlist')

            assert result is not None
            assert result['id'] == 'cached_123'
            # Should not call Spotify API
            mock_spotify_client.current_user_playlists.assert_not_called()

    def test_find_in_api_when_not_in_cache(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Find playlist via API when not in cache."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client

        # Mock API response
        mock_spotify_client.current_user_playlists.return_value = {
            'items': [
                {'id': 'api_123', 'name': 'Test Playlist'},
                {'id': 'api_456', 'name': 'Other Playlist'}
            ],
            'next': None
        }

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.find_by_name('Test Playlist')

            assert result is not None
            assert result['id'] == 'api_123'
            assert result['name'] == 'Test Playlist'

    def test_find_case_insensitive(self, mock_spotify_auth, temp_cache_dir):
        """Find is case insensitive."""
        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)
            manager._playlist_cache['test playlist'] = {
                'id': 'cached_123',
                'name': 'Test Playlist'
            }

            # Try different cases
            result1 = manager.find_by_name('TEST PLAYLIST')
            result2 = manager.find_by_name('test playlist')
            result3 = manager.find_by_name('Test Playlist')

            assert result1 is not None
            assert result2 is not None
            assert result3 is not None
            assert result1['id'] == result2['id'] == result3['id']

    def test_find_not_found(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Returns None when playlist not found."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.current_user_playlists.return_value = {
            'items': [],
            'next': None
        }

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.find_by_name('Nonexistent')

            assert result is None

    def test_find_pagination(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Find handles pagination correctly."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client

        # First page - no match
        first_page = {
            'items': [{'id': '1', 'name': 'Playlist 1'}],
            'next': 'next_page_url'
        }

        # Second page - has match
        second_page = {
            'items': [{'id': '2', 'name': 'Target Playlist'}],
            'next': None
        }

        mock_spotify_client.current_user_playlists.return_value = first_page
        mock_spotify_client.current_user_playlists.side_effect = [first_page, second_page]

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.find_by_name('Target Playlist')

            assert result is not None
            assert result['id'] == '2'


class TestPlaylistManagerClear:
    """Test clearing playlists."""

    def test_clear_empty_playlist(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Clear empty playlist."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.playlist_tracks.return_value = {
            'items': [],
            'next': None
        }

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.clear('playlist_123')

            assert result is True

    def test_clear_playlist_with_tracks(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Clear playlist with tracks."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.playlist_tracks.return_value = {
            'items': [
                {'track': {'uri': 'spotify:track:1'}},
                {'track': {'uri': 'spotify:track:2'}},
            ],
            'next': None
        }

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.clear('playlist_123')

            assert result is True
            mock_spotify_client.playlist_remove_all_occurrences_of_items.assert_called_once()

    def test_clear_failure(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Clear returns False on failure."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.playlist_tracks.side_effect = Exception('API Error')

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.clear('playlist_123')

            assert result is False


class TestPlaylistManagerUpdateDetails:
    """Test updating playlist details."""

    def test_update_description(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Update playlist description."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.update_details('playlist_123', description='New Description')

            assert result is True
            mock_spotify_client.playlist_change_details.assert_called_once_with(
                'playlist_123',
                description='New Description'
            )

    def test_update_no_description(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Update with no description returns False."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            result = manager.update_details('playlist_123', description=None)

            assert result is False
            mock_spotify_client.playlist_change_details.assert_not_called()


class TestPlaylistManagerGetAll:
    """Test getting all playlists."""

    def test_get_all(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Get all playlists."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.current_user_playlists.return_value = {
            'items': [
                {'id': '1', 'name': 'Playlist 1'},
                {'id': '2', 'name': 'Playlist 2'},
            ]
        }

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            playlists = manager.get_all(limit=50)

            assert len(playlists) == 2
            assert playlists[0]['id'] == '1'
            assert playlists[1]['id'] == '2'

    def test_get_all_failure(self, mock_spotify_auth, mock_spotify_client, temp_cache_dir):
        """Get all returns empty list on failure."""
        mock_spotify_auth.get_client.return_value = mock_spotify_client
        mock_spotify_client.current_user_playlists.side_effect = Exception('API Error')

        with patch.object(Path, 'home', return_value=temp_cache_dir.parent.parent):
            manager = PlaylistManager(mock_spotify_auth)

            playlists = manager.get_all()

            assert playlists == []
