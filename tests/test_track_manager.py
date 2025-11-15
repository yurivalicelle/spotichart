"""Tests for the TrackManager."""

import pytest
from unittest.mock import Mock
from spotichart.core.track_manager import TrackManager
from spotichart.utils.exceptions import TrackAdditionError

@pytest.fixture
def mock_spotify_client():
    """Provides a mock ISpotifyClient."""
    client = Mock()
    client.playlist_add_items = Mock()
    return client

class TestTrackManagerInit:
    """Tests for TrackManager initialization."""

    def test_init_with_client(self, mock_spotify_client):
        """TrackManager should initialize with a client."""
        manager = TrackManager(mock_spotify_client)
        assert manager.client == mock_spotify_client

class TestTrackManagerBuildUri:
    """Tests for the build_uri method."""

    def test_build_uri_correctly(self, mock_spotify_client):
        """Should build a valid Spotify track URI."""
        manager = TrackManager(mock_spotify_client)
        track_id = "12345abcde"
        expected_uri = "spotify:track:12345abcde"
        assert manager.build_uri(track_id) == expected_uri

class TestTrackManagerAddToPlaylist:
    """Tests for adding tracks to a playlist."""

    def test_add_to_playlist_success(self, mock_spotify_client):
        """Should add tracks to a playlist in batches."""
        manager = TrackManager(mock_spotify_client)
        track_uris = [f"spotify:track:{i}" for i in range(150)]

        added_count = manager.add_to_playlist('p_123', track_uris)

        assert added_count == 150
        # Should be called twice: once for the first 100, once for the remaining 50
        assert mock_spotify_client.playlist_add_items.call_count == 2
        mock_spotify_client.playlist_add_items.assert_any_call('p_123', track_uris[:100])
        mock_spotify_client.playlist_add_items.assert_any_call('p_123', track_uris[100:])

    def test_add_to_playlist_empty_list(self, mock_spotify_client):
        """Should do nothing if the track list is empty."""
        manager = TrackManager(mock_spotify_client)
        added_count = manager.add_to_playlist('p_123', [])

        assert added_count == 0
        mock_spotify_client.playlist_add_items.assert_not_called()

    def test_add_to_playlist_api_failure(self, mock_spotify_client):
        """Should raise TrackAdditionError on API failure."""
        mock_spotify_client.playlist_add_items.side_effect = Exception("API Error")
        manager = TrackManager(mock_spotify_client)
        track_uris = ["spotify:track:1"]

        with pytest.raises(TrackAdditionError, match="Failed to add tracks"):
            manager.add_to_playlist('p_123', track_uris)
