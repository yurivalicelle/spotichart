"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from datetime import datetime
import tempfile
import json


# ============================================================================
# Mock Spotify Client Fixtures
# ============================================================================

@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client (spotipy.Spotify)."""
    mock_sp = Mock()

    # Mock user info
    mock_sp.me.return_value = {
        'id': 'test_user_123',
        'display_name': 'Test User',
        'email': 'test@example.com'
    }

    # Mock playlist creation
    mock_sp.user_playlist_create.return_value = {
        'id': 'playlist_123',
        'name': 'Test Playlist',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/playlist_123'},
        'tracks': {'total': 0}
    }

    # Mock playlist tracks
    mock_sp.playlist_tracks.return_value = {
        'items': [],
        'next': None
    }

    # Mock current user playlists
    mock_sp.current_user_playlists.return_value = {
        'items': [],
        'next': None
    }

    # Mock track lookup
    mock_sp.track.return_value = {
        'id': 'track_123',
        'name': 'Test Track',
        'artists': [{'name': 'Test Artist'}]
    }

    # Mock playlist operations
    mock_sp.playlist_add_items.return_value = None
    mock_sp.playlist_remove_all_occurrences_of_items.return_value = None
    mock_sp.playlist_change_details.return_value = None

    return mock_sp


@pytest.fixture
def mock_auth_manager():
    """Mock Spotify OAuth manager."""
    mock_auth = Mock()
    mock_auth.get_access_token.return_value = {
        'access_token': 'mock_token_123',
        'expires_at': 9999999999
    }
    return mock_auth


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = Mock()
    config.SPOTIFY_CLIENT_ID = 'test_client_id'
    config.SPOTIFY_CLIENT_SECRET = 'test_client_secret'
    config.REDIRECT_URI = 'http://localhost:8888/callback'
    config.SPOTIFY_SCOPE = 'playlist-modify-private playlist-modify-public'
    config.SPOTIFY_BATCH_SIZE = 100
    config.REQUEST_TIMEOUT = 30
    config.DEFAULT_PLAYLIST_LIMIT = 1000
    config.CACHE_DIR = Path(tempfile.gettempdir()) / 'test_cache'
    config.LOG_DIR = Path(tempfile.gettempdir()) / 'test_logs'
    return config


@pytest.fixture
def config_dict():
    """Configuration dictionary for testing."""
    return {
        'SPOTIFY_CLIENT_ID': 'test_client_id',
        'SPOTIFY_CLIENT_SECRET': 'test_client_secret',
        'REDIRECT_URI': 'http://localhost:8888/callback',
        'SPOTIFY_SCOPE': 'playlist-modify-private playlist-modify-public',
        'SPOTIFY_BATCH_SIZE': 100,
        'REQUEST_TIMEOUT': 30,
        'DEFAULT_PLAYLIST_LIMIT': 1000,
    }


# ============================================================================
# Interface Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_config_interface():
    """Mock IConfiguration implementation."""
    mock = Mock()
    mock.get.side_effect = lambda key, default=None: {
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'redirect_uri': 'http://localhost:8888/callback',
        'scope': 'playlist-modify-private',
    }.get(key, default)
    mock.validate.return_value = True
    return mock


@pytest.fixture
def mock_spotify_auth():
    """Mock ISpotifyAuth implementation."""
    mock = Mock()
    mock.get_client.return_value = Mock()  # Returns mock Spotify client
    mock.get_user_id.return_value = 'test_user_123'
    return mock


@pytest.fixture
def mock_playlist_operations():
    """Mock IPlaylistOperations implementation."""
    mock = Mock()
    mock.create.return_value = {
        'id': 'playlist_123',
        'name': 'Test Playlist',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/playlist_123'}
    }
    mock.find_by_name.return_value = None
    mock.clear.return_value = True
    mock.update_details.return_value = True
    mock.get_all.return_value = []
    return mock


@pytest.fixture
def mock_track_operations():
    """Mock ITrackOperations implementation."""
    mock = Mock()
    mock.add_to_playlist.return_value = 10
    mock.search.return_value = {'id': 'track_123', 'name': 'Test Track'}
    mock.build_uri.return_value = 'spotify:track:track_123'
    return mock


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory."""
    cache_dir = tmp_path / '.spotify_playlist_creator' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def temp_config_file(tmp_path):
    """Temporary JSON config file."""
    config_file = tmp_path / 'config.json'
    config_data = {
        'spotify': {
            'client_id': 'json_client_id',
            'client_secret': 'json_client_secret',
        }
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    return config_file


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_tracks():
    """Sample track IDs for testing."""
    return [
        '6rqhFgbbKwnb9MLmUQDhG6',  # Track 1
        '3n3Ppam7vgaVa1iaRUc9Lp',  # Track 2
        '37ZJ0p5Jm13JPevGcx4SkF',  # Track 3
        '0VjIjW4GlUZAMYd2vXMi3b',  # Track 4
        '2takcwOaAZWiXQijPHIx7B',  # Track 5
    ]


@pytest.fixture
def sample_playlist_data():
    """Sample playlist data."""
    return {
        'id': 'playlist_abc123',
        'name': 'Sample Playlist',
        'description': 'A test playlist',
        'external_urls': {'spotify': 'https://open.spotify.com/playlist/playlist_abc123'},
        'public': False,
        'tracks': {'total': 5}
    }


@pytest.fixture
def sample_cache_data():
    """Sample cache data for playlist cache testing."""
    return {
        'test playlist': {
            'playlist': {
                'id': 'cached_playlist_123',
                'name': 'Test Playlist',
                'external_urls': {'spotify': 'https://open.spotify.com/playlist/cached_playlist_123'}
            },
            'cached_at': datetime.now().isoformat()
        }
    }


# ============================================================================
# HTML Mock Fixtures (for scraper testing)
# ============================================================================

@pytest.fixture
def mock_kworb_html():
    """Mock HTML response from Kworb."""
    return """
    <html>
        <body>
            <table>
                <tr>
                    <td>1</td>
                    <td><a href="/spotify/track/123">Track One</a></td>
                    <td>Artist One</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td><a href="/spotify/track/456">Track Two</a></td>
                    <td>Artist Two</td>
                </tr>
                <tr>
                    <td>3</td>
                    <td><a href="/spotify/track/789">Track Three</a></td>
                    <td>Artist Three</td>
                </tr>
            </table>
        </body>
    </html>
    """


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Automatically cleanup temporary files after each test."""
    yield
    # Cleanup happens automatically with tmp_path
