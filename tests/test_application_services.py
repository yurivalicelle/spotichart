"""
Tests for Application Services (TDD Approach).

Testing the facade layer that orchestrates commands and handlers.
"""

from unittest.mock import Mock

import pytest

from spotichart.application.services import PlaylistApplicationService
from spotichart.core.models import Track
from spotichart.utils.result import Failure, Success


class TestPlaylistApplicationService:
    """Tests for PlaylistApplicationService using TDD."""

    def test_create_playlist_from_charts_delegates_to_handler(self):
        """Test that create_playlist_from_charts delegates to handler correctly."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()
        mock_event_bus = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
            event_bus=mock_event_bus,
        )

        # Mock the handler's response
        tracks = [Track(id="track1", name="Song", artist="Artist")]
        mock_chart_provider.get_charts.return_value = Success(tracks)
        mock_playlist_ops.find_by_name.return_value = None
        mock_playlist_ops.create.return_value = {
            "id": "playlist123",
            "external_urls": {"spotify": "https://spotify.com/playlist/123"},
        }
        mock_track_ops.build_uri.side_effect = lambda tid: f"spotify:track:{tid}"

        # Act
        result = service.create_playlist_from_charts(
            region="brazil",
            limit=50,
            name="Top Brazil",
            public=True,
            update_mode="replace",
            description="Test playlist",
        )

        # Assert
        assert result.is_success()
        response = result.unwrap()
        assert response.playlist_url == "https://spotify.com/playlist/123"

        # Verify chart provider was called
        mock_chart_provider.get_charts.assert_called_once_with("brazil", 50)

    def test_create_playlist_with_append_mode(self):
        """Test create playlist with append update mode."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        tracks = [Track(id="track1", name="Song", artist="Artist")]
        mock_chart_provider.get_charts.return_value = Success(tracks)
        mock_playlist_ops.find_by_name.return_value = {
            "id": "existing123",
            "external_urls": {"spotify": "https://spotify.com/playlist/existing"},
        }
        mock_track_ops.build_uri.side_effect = lambda tid: f"spotify:track:{tid}"

        # Act
        result = service.create_playlist_from_charts(
            region="global",
            limit=100,
            name="Existing Playlist",
            public=False,
            update_mode="append",
        )

        # Assert
        assert result.is_success()
        response = result.unwrap()
        assert response.was_updated is True
        # Should NOT clear in append mode
        mock_playlist_ops.clear.assert_not_called()

    def test_preview_charts_delegates_to_handler(self):
        """Test that preview_charts delegates to handler correctly."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        tracks = [Track(id="track1", name="Song", artist="Artist")]
        mock_chart_provider.get_charts.return_value = Success(tracks)

        # Act
        result = service.preview_charts(region="us", limit=20)

        # Assert
        assert result.is_success()
        response = result.unwrap()
        assert response.region == "us"
        assert len(response.tracks) == 1
        mock_chart_provider.get_charts.assert_called_once_with("us", 20)

    def test_preview_charts_with_default_limit(self):
        """Test preview_charts with default limit."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        mock_chart_provider.get_charts.return_value = Success([])

        # Act
        result = service.preview_charts(region="global")

        # Assert
        mock_chart_provider.get_charts.assert_called_once_with("global", 50)

    def test_list_playlists_delegates_to_handler(self):
        """Test that list_playlists delegates to handler correctly."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        mock_playlist_ops.get_all.return_value = [
            {
                "id": "1",
                "name": "Playlist 1",
                "tracks": {"total": 10},
                "public": True,
                "external_urls": {"spotify": "url1"},
            }
        ]

        # Act
        result = service.list_playlists(limit=10)

        # Assert
        assert result.is_success()
        response = result.unwrap()
        assert len(response.playlists) == 1
        mock_playlist_ops.get_all.assert_called_once_with(10)

    def test_list_playlists_with_default_limit(self):
        """Test list_playlists with default limit."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        mock_playlist_ops.get_all.return_value = []

        # Act
        result = service.list_playlists()

        # Assert
        mock_playlist_ops.get_all.assert_called_once_with(50)

    def test_list_available_regions_delegates_to_handler(self):
        """Test that list_available_regions delegates to handler correctly."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        mock_chart_provider.get_available_regions.return_value = ["brazil", "us", "global"]

        # Act
        result = service.list_available_regions()

        # Assert
        assert result.is_success()
        response = result.unwrap()
        assert len(response.regions) == 3
        assert response.regions[0].name == "brazil"

    def test_get_event_bus_returns_bus_instance(self):
        """Test that get_event_bus returns the event bus."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()
        mock_event_bus = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
            event_bus=mock_event_bus,
        )

        # Act
        bus = service.get_event_bus()

        # Assert
        assert bus == mock_event_bus

    def test_cleanup_closes_chart_provider(self):
        """Test that cleanup closes the chart provider."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        # Act
        service.cleanup()

        # Assert
        mock_chart_provider.close.assert_called_once()

    def test_cleanup_handles_errors_gracefully(self):
        """Test that cleanup handles errors without raising."""
        # Arrange
        mock_chart_provider = Mock()
        mock_chart_provider.close.side_effect = Exception("Close error")
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        # Act - Should not raise
        service.cleanup()

        # Assert
        mock_chart_provider.close.assert_called_once()

    def test_service_creates_event_bus_if_not_provided(self):
        """Test that service creates event bus if not provided."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        # Act - No event_bus provided
        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        # Assert
        bus = service.get_event_bus()
        assert bus is not None
        from spotichart.application.events import EventBus

        assert isinstance(bus, EventBus)

    def test_error_propagation_from_chart_provider(self):
        """Test that errors from chart provider are propagated."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        mock_chart_provider.get_charts.return_value = Failure(Exception("Chart error"))

        # Act
        result = service.create_playlist_from_charts(
            region="invalid", limit=50, name="Test", public=False, update_mode="replace"
        )

        # Assert
        assert result.is_failure()

    def test_error_propagation_from_playlist_operations(self):
        """Test that errors from playlist operations are propagated."""
        # Arrange
        mock_chart_provider = Mock()
        mock_playlist_ops = Mock()
        mock_track_ops = Mock()

        service = PlaylistApplicationService(
            chart_provider=mock_chart_provider,
            playlist_ops=mock_playlist_ops,
            track_ops=mock_track_ops,
        )

        tracks = [Track(id="track1", name="Song", artist="Artist")]
        mock_chart_provider.get_charts.return_value = Success(tracks)
        mock_playlist_ops.find_by_name.side_effect = Exception("Playlist error")

        # Act
        result = service.create_playlist_from_charts(
            region="brazil", limit=50, name="Test", public=False, update_mode="replace"
        )

        # Assert
        assert result.is_failure()
