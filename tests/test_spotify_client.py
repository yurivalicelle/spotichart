"""
Tests for the refactored SpotifyClient with dependency injection.
SpotifyClient is now a simple wrapper implementing ISpotifyClient interface.
"""

from unittest.mock import MagicMock, Mock

import pytest

from spotichart.core.spotify_authenticator import SpotifyAuthenticator
from spotichart.core.spotify_client import SpotifyClient


@pytest.fixture
def mock_authenticator():
    """Provides a mock SpotifyAuthenticator."""
    authenticator = Mock(spec=SpotifyAuthenticator)
    authenticator.get_user_id.return_value = "user_123"

    # Mock spotipy.Spotify instance
    mock_sp = MagicMock()
    mock_sp.me.return_value = {"id": "user_123"}
    authenticator.get_client.return_value = mock_sp

    return authenticator


@pytest.fixture
def sp_instance(mock_authenticator):
    """Provides direct access to the mocked spotipy.Spotify instance."""
    return mock_authenticator.get_client.return_value


@pytest.fixture
def client(mock_authenticator):
    """Provides a fresh SpotifyClient instance for each test."""
    return SpotifyClient(authenticator=mock_authenticator)


class TestSpotifyClientInit:
    """Tests for SpotifyClient initialization."""

    def test_init_with_authenticator(self, mock_authenticator):
        """Should initialize with authenticator dependency."""
        client = SpotifyClient(authenticator=mock_authenticator)
        assert client._authenticator == mock_authenticator


class TestSpotifyClientAuth:
    """Tests for authentication-related properties."""

    def test_user_id_delegates_to_authenticator(self, client, mock_authenticator):
        """Should delegate user_id to authenticator."""
        user_id = client.user_id
        assert user_id == "user_123"
        mock_authenticator.get_user_id.assert_called_once()

    def test_sp_property_lazy_loads(self, client, mock_authenticator):
        """Should lazy-load spotify client from authenticator."""
        sp = client.sp
        mock_authenticator.get_client.assert_called_once()

        # Second access should not call authenticator again
        sp2 = client.sp
        assert mock_authenticator.get_client.call_count == 1
        assert sp == sp2


class TestSpotifyClientPlaylistOperations:
    """Tests for basic playlist operations (delegated to spotipy)."""

    def test_user_playlist_create(self, client, sp_instance):
        """Should delegate playlist creation to spotipy."""
        sp_instance.user_playlist_create.return_value = {"id": "p_123", "name": "Test"}

        playlist = client.user_playlist_create(
            user="user_123", name="Test", public=False, description="Description"
        )

        assert playlist["id"] == "p_123"
        sp_instance.user_playlist_create.assert_called_once_with(
            user="user_123", name="Test", public=False, description="Description"
        )

    def test_current_user_playlists(self, client, sp_instance):
        """Should delegate getting playlists to spotipy."""
        sp_instance.current_user_playlists.return_value = {"items": [{"id": "p1"}, {"id": "p2"}]}

        result = client.current_user_playlists(limit=50, offset=0)

        assert len(result["items"]) == 2
        sp_instance.current_user_playlists.assert_called_once_with(limit=50, offset=0)

    def test_playlist_tracks(self, client, sp_instance):
        """Should delegate getting playlist tracks to spotipy."""
        sp_instance.playlist_tracks.return_value = {"items": [{"track": {"id": "t1"}}]}

        result = client.playlist_tracks("p_123")

        assert len(result["items"]) == 1
        sp_instance.playlist_tracks.assert_called_once_with("p_123")

    def test_playlist_remove_all_occurrences_of_items(self, client, sp_instance):
        """Should delegate removing tracks to spotipy."""
        sp_instance.playlist_remove_all_occurrences_of_items.return_value = {}

        client.playlist_remove_all_occurrences_of_items("p_123", ["uri1", "uri2"])

        sp_instance.playlist_remove_all_occurrences_of_items.assert_called_once_with(
            "p_123", ["uri1", "uri2"]
        )

    def test_playlist_change_details(self, client, sp_instance):
        """Should delegate changing playlist details to spotipy."""
        client.playlist_change_details("p_123", description="New Description")

        sp_instance.playlist_change_details.assert_called_once_with(
            playlist_id="p_123",
            name=None,
            public=None,
            collaborative=None,
            description="New Description",
        )

    def test_next(self, client, sp_instance):
        """Should delegate pagination to spotipy."""
        mock_result = {"items": [], "next": "next_url"}
        sp_instance.next.return_value = {"items": [{"id": "next_item"}]}

        result = client.next(mock_result)

        sp_instance.next.assert_called_once_with(mock_result)
        assert result["items"][0]["id"] == "next_item"


class TestSpotifyClientTrackOperations:
    """Tests for basic track operations (delegated to spotipy)."""

    def test_playlist_add_items(self, client, sp_instance):
        """Should delegate adding tracks to spotipy."""
        sp_instance.playlist_add_items.return_value = {}

        client.playlist_add_items("p_123", ["uri1", "uri2"])

        sp_instance.playlist_add_items.assert_called_once_with("p_123", ["uri1", "uri2"], None)

    def test_track(self, client, sp_instance):
        """Should delegate track lookup to spotipy."""
        sp_instance.track.return_value = {"id": "t_123", "name": "Track"}

        result = client.track("t_123")

        assert result["id"] == "t_123"
        sp_instance.track.assert_called_once_with(track_id="t_123")

    def test_track_not_found(self, client, sp_instance):
        """Should return None when track is not found."""
        sp_instance.track.side_effect = Exception("Not Found")

        result = client.track("invalid_id")

        assert result is None
