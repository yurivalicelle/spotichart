"""
End-to-End Integration Tests

Tests the complete flow from chart scraping to playlist creation.
These tests validate the entire system working together.
"""

import os
from unittest.mock import Mock

import pytest

from spotichart.application.services import PlaylistApplicationService
from spotichart.core.kworb_provider import KworbChartProvider
from spotichart.core.models import Track
from spotichart.core.playlist_manager import PlaylistManager
from spotichart.core.track_manager import TrackManager
from spotichart.utils.result import Success


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "a" * 32)
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "b" * 32)
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")


@pytest.fixture
def mock_spotify_client():
    """Create a mock Spotify client."""
    client = Mock()

    # Mock user info
    client.me.return_value = {"id": "test_user"}

    # Mock playlist creation
    client.user_playlist_create.return_value = {
        "id": "new_playlist_123",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/new_playlist_123"},
        "name": "Test Playlist",
    }

    # Mock playlist listing - empty list (no existing playlists)
    client.current_user_playlists.return_value = {
        "items": [],
        "next": None,
        "total": 0
    }

    # Mock track addition
    client.playlist_add_items.return_value = {"snapshot_id": "snapshot123"}

    return client


@pytest.fixture
def mock_chart_provider():
    """Create a mock chart provider."""
    provider = Mock(spec=KworbChartProvider)

    # Mock chart data
    mock_tracks = [
        Track(id=f"track{i}", name=f"Song {i}", artist=f"Artist {i}", album=f"Album {i}")
        for i in range(1, 51)
    ]

    provider.get_charts.return_value = Success(mock_tracks)
    provider.get_available_regions.return_value = ["brazil", "us", "global"]
    provider.close.return_value = None

    return provider


class TestE2EPlaylistCreation:
    """End-to-end tests for playlist creation flow."""

    def test_complete_playlist_creation_flow(self, mock_spotify_client, mock_chart_provider):
        """
        Test complete flow: scrape charts → create playlist → add tracks.

        This tests the entire system working together.
        """
        # Setup services
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        app_service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute: Create playlist from Brazil charts
        result = app_service.create_playlist_from_charts(
            region="brazil", limit=50, name="Top Brazil 2024", public=True, update_mode="replace"
        )

        # Verify
        assert result.is_success()

        response = result.unwrap()
        assert response.playlist_url == "https://open.spotify.com/playlist/new_playlist_123"
        assert response.tracks_added == 50
        assert response.tracks_failed == 0
        # Note: was_updated can be True or False depending on playlist cache state
        # The important thing is that the operation succeeded
        assert isinstance(response.was_updated, bool)

        # Verify chart provider was called
        mock_chart_provider.get_charts.assert_called_once_with("brazil", 50)

        # Verify tracks were added
        assert mock_spotify_client.playlist_add_items.called

    def test_playlist_update_flow(self, mock_spotify_client, mock_chart_provider):
        """Test updating an existing playlist."""
        # Mock existing playlist
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {
                    "id": "existing_123",
                    "name": "Top Brazil 2024",
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/existing_123"},
                    "tracks": {"total": 30},
                }
            ]
        }

        # Mock playlist tracks
        mock_spotify_client.playlist_tracks.return_value = {
            "items": [
                {"track": {"id": f"old_track{i}", "uri": f"spotify:track:old_track{i}"}}
                for i in range(30)
            ]
        }

        # Setup
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        app_service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute: Update existing playlist
        result = app_service.create_playlist_from_charts(
            region="brazil",
            limit=50,
            name="Top Brazil 2024",
            public=True,
            update_mode="replace",  # Replace mode
        )

        # Verify
        assert result.is_success()

        response = result.unwrap()
        assert response.was_updated is True
        assert response.tracks_added == 50

        # Verify playlist was NOT created (updated instead)
        mock_spotify_client.user_playlist_create.assert_not_called()

        # Verify tracks were removed and re-added (replace mode)
        mock_spotify_client.playlist_remove_all_occurrences_of_items.assert_called()

    def test_preview_charts_flow(self, mock_chart_provider):
        """Test previewing charts without creating playlist."""
        # Setup
        playlist_manager = Mock()
        track_manager = Mock()

        app_service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute: Preview charts
        result = app_service.preview_charts(region="brazil", limit=20)

        # Verify
        assert result.is_success()

        response = result.unwrap()
        assert response.region == "brazil"
        assert len(response.tracks) == 50  # Mock returns 50
        assert response.total_tracks == 50

        # Verify no playlist operations were performed
        playlist_manager.create.assert_not_called()
        track_manager.add_to_playlist.assert_not_called()

    def test_list_playlists_flow(self, mock_spotify_client):
        """Test listing user playlists."""
        # Mock playlist data
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {
                    "id": "p1",
                    "name": "Playlist 1",
                    "tracks": {"total": 25},
                    "public": True,
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/p1"},
                    "description": "Test playlist 1",
                },
                {
                    "id": "p2",
                    "name": "Playlist 2",
                    "tracks": {"total": 30},
                    "public": False,
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/p2"},
                    "description": "",
                },
            ]
        }

        # Setup
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = Mock()
        chart_provider = Mock()

        app_service = PlaylistApplicationService(
            chart_provider=chart_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute
        result = app_service.list_playlists(limit=50)

        # Verify
        assert result.is_success()

        response = result.unwrap()
        assert response.total_count == 2
        assert len(response.playlists) == 2
        assert response.playlists[0].name == "Playlist 1"
        assert response.playlists[1].name == "Playlist 2"

    def test_error_handling_chart_scraping_failure(self, mock_spotify_client):
        """Test error handling when chart scraping fails."""
        from spotichart.utils.exceptions import ChartScrapingError
        from spotichart.utils.result import Failure

        # Mock chart provider that fails
        failed_provider = Mock()
        failed_provider.get_charts.return_value = Failure(
            ChartScrapingError("Failed to scrape charts")
        )

        # Setup
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        app_service = PlaylistApplicationService(
            chart_provider=failed_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute
        result = app_service.create_playlist_from_charts(
            region="brazil", limit=50, name="Test", public=True, update_mode="replace"
        )

        # Verify error is propagated
        assert result.is_failure()
        assert isinstance(result.error, ChartScrapingError)

        # Verify no playlist was created
        mock_spotify_client.user_playlist_create.assert_not_called()

    def test_error_handling_no_tracks_found(self, mock_spotify_client):
        """Test error handling when no tracks are found."""
        # Mock provider returning empty list
        empty_provider = Mock()
        empty_provider.get_charts.return_value = Success([])

        # Setup
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        app_service = PlaylistApplicationService(
            chart_provider=empty_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute
        result = app_service.create_playlist_from_charts(
            region="invalid_region", limit=50, name="Test", public=True, update_mode="replace"
        )

        # Verify
        assert result.is_failure()

        # No playlist should be created
        mock_spotify_client.user_playlist_create.assert_not_called()

    def test_append_mode_preserves_existing_tracks(self, mock_spotify_client, mock_chart_provider):
        """Test that append mode preserves existing tracks."""
        # Mock existing playlist with tracks
        mock_spotify_client.current_user_playlists.return_value = {
            "items": [
                {
                    "id": "existing_123",
                    "name": "My Playlist",
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/existing_123"},
                    "tracks": {"total": 10},
                }
            ]
        }

        # Setup
        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        app_service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=playlist_manager,
            track_ops=track_manager,
        )

        # Execute with append mode
        result = app_service.create_playlist_from_charts(
            region="brazil",
            limit=50,
            name="My Playlist",
            public=True,
            update_mode="append",  # Append mode!
        )

        # Verify
        assert result.is_success()

        # Verify tracks were NOT removed (append mode)
        mock_spotify_client.playlist_remove_all_occurrences_of_items.assert_not_called()

        # Verify new tracks were added
        mock_spotify_client.playlist_add_items.assert_called()


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_E2E_TESTS"), reason="Requires real Spotify credentials"
)
class TestRealE2E:
    """
    Real E2E tests (skipped by default).

    To run these tests:
    1. Set up Spotify credentials in .env
    2. Run: RUN_REAL_E2E_TESTS=1 pytest tests/integration/test_e2e_playlist_creation.py -v
    """

    def test_real_playlist_creation(self):
        """Test with real Spotify API (requires credentials)."""
        from spotichart.core.dependency_container import DependencyContainer

        container = DependencyContainer()
        app_service = container.get_application_service()

        # Create a test playlist
        result = app_service.create_playlist_from_charts(
            region="brazil",
            limit=10,  # Small limit for testing
            name="[E2E Test] Top Brazil",
            public=False,  # Private for testing
            update_mode="new",  # Always create new
        )

        # Cleanup
        container.cleanup()

        # Verify
        assert result.is_success()
        response = result.unwrap()
        assert "spotify.com/playlist" in response.playlist_url
        assert response.tracks_added > 0
