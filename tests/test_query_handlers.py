"""
Tests for Query Handlers (CQRS)
"""

from unittest.mock import Mock, patch

import pytest

from spotichart.application.dtos import (
    ChartPreviewResponse,
    PlaylistListItem,
    PlaylistListResponse,
    RegionInfo,
    RegionListResponse,
)
from spotichart.application.events import EventBus
from spotichart.application.queries import (
    GetPlaylistByIdQuery,
    GetPlaylistByNameQuery,
    GetPlaylistStatisticsQuery,
    GetPlaylistTracksQuery,
    ListPlaylistsQuery,
    ListRegionsQuery,
    PreviewChartsQuery,
    SearchPlaylistsQuery,
)
from spotichart.application.query_handlers import (
    GetPlaylistByIdQueryHandler,
    GetPlaylistByNameQueryHandler,
    GetPlaylistStatisticsQueryHandler,
    GetPlaylistTracksQueryHandler,
    ListPlaylistsQueryHandler,
    ListRegionsQueryHandler,
    PreviewChartsQueryHandler,
    SearchPlaylistsQueryHandler,
)
from spotichart.core.models import Track
from spotichart.utils.exceptions import PlaylistNotFoundError
from spotichart.utils.result import Failure, Success


class TestGetPlaylistByIdQueryHandler:
    """Test GetPlaylistByIdQueryHandler."""

    def test_handle_found(self):
        """Test handling when playlist is found."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [
                {"id": "playlist1", "name": "Test Playlist"},
                {"id": "playlist2", "name": "Other Playlist"},
            ]
        }

        handler = GetPlaylistByIdQueryHandler(playlist_reader)
        query = GetPlaylistByIdQuery(playlist_id="playlist1")

        result = handler.handle(query)

        assert result.is_success()
        data = result.unwrap()
        assert data["id"] == "playlist1"
        assert data["name"] == "Test Playlist"

    def test_handle_not_found(self):
        """Test handling when playlist is not found."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.return_value = {
            "items": [{"id": "other", "name": "Other"}]
        }

        handler = GetPlaylistByIdQueryHandler(playlist_reader)
        query = GetPlaylistByIdQuery(playlist_id="nonexistent")

        result = handler.handle(query)

        assert result.is_failure()
        assert isinstance(result.error, PlaylistNotFoundError)

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_reader = Mock()
        playlist_reader.current_user_playlists.side_effect = Exception("API error")

        handler = GetPlaylistByIdQueryHandler(playlist_reader)
        query = GetPlaylistByIdQuery(playlist_id="test")

        result = handler.handle(query)

        assert result.is_failure()
        assert isinstance(result.error, Exception)


class TestGetPlaylistByNameQueryHandler:
    """Test GetPlaylistByNameQueryHandler."""

    def test_handle_found(self):
        """Test handling when playlist is found."""
        playlist_ops = Mock()
        playlist_ops.find_by_name.return_value = {"id": "test_id", "name": "Test"}

        handler = GetPlaylistByNameQueryHandler(playlist_ops)
        query = GetPlaylistByNameQuery(name="Test")

        result = handler.handle(query)

        assert result.is_success()
        assert result.unwrap()["id"] == "test_id"

    def test_handle_not_found(self):
        """Test handling when playlist is not found."""
        playlist_ops = Mock()
        playlist_ops.find_by_name.return_value = None

        handler = GetPlaylistByNameQueryHandler(playlist_ops)
        query = GetPlaylistByNameQuery(name="Nonexistent")

        result = handler.handle(query)

        assert result.is_success()
        assert result.unwrap() is None

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_ops = Mock()
        playlist_ops.find_by_name.side_effect = Exception("Error")

        handler = GetPlaylistByNameQueryHandler(playlist_ops)
        query = GetPlaylistByNameQuery(name="Test")

        result = handler.handle(query)

        assert result.is_failure()


class TestListPlaylistsQueryHandler:
    """Test ListPlaylistsQueryHandler."""

    def test_handle_success(self):
        """Test successful playlist listing."""
        playlist_ops = Mock()
        playlist_ops.get_all.return_value = [
            {
                "id": "p1",
                "name": "Playlist 1",
                "tracks": {"total": 10},
                "public": True,
                "external_urls": {"spotify": "https://spotify.com/p1"},
                "description": "Test playlist",
            }
        ]

        handler = ListPlaylistsQueryHandler(playlist_ops)
        query = ListPlaylistsQuery(limit=10)

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert isinstance(response, PlaylistListResponse)
        assert response.total_count == 1
        assert len(response.playlists) == 1
        assert response.playlists[0].id == "p1"

    def test_handle_empty_list(self):
        """Test handling empty playlist list."""
        playlist_ops = Mock()
        playlist_ops.get_all.return_value = []

        handler = ListPlaylistsQueryHandler(playlist_ops)
        query = ListPlaylistsQuery()

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert response.total_count == 0
        assert len(response.playlists) == 0

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_ops = Mock()
        playlist_ops.get_all.side_effect = Exception("API error")

        handler = ListPlaylistsQueryHandler(playlist_ops)
        query = ListPlaylistsQuery()

        result = handler.handle(query)

        assert result.is_failure()


class TestGetPlaylistTracksQueryHandler:
    """Test GetPlaylistTracksQueryHandler."""

    def test_handle_success(self):
        """Test successful track fetching."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {
                    "track": {
                        "id": "track1",
                        "name": "Song 1",
                        "artists": [{"name": "Artist 1"}],
                        "album": {"name": "Album 1"},
                    }
                }
            ]
        }

        handler = GetPlaylistTracksQueryHandler(playlist_reader)
        query = GetPlaylistTracksQuery(playlist_id="test_id")

        result = handler.handle(query)

        assert result.is_success()
        tracks = result.unwrap()
        assert len(tracks) == 1
        assert isinstance(tracks[0], Track)
        assert tracks[0].id == "track1"

    def test_handle_limit(self):
        """Test that limit is respected."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {"track": {"id": f"t{i}", "name": f"Song {i}", "artists": [{"name": "Artist"}]}}
                for i in range(10)
            ]
        }

        handler = GetPlaylistTracksQueryHandler(playlist_reader)
        query = GetPlaylistTracksQuery(playlist_id="test_id", limit=5)

        result = handler.handle(query)

        assert result.is_success()
        tracks = result.unwrap()
        assert len(tracks) == 5

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.side_effect = Exception("Error")

        handler = GetPlaylistTracksQueryHandler(playlist_reader)
        query = GetPlaylistTracksQuery(playlist_id="test_id")

        result = handler.handle(query)

        assert result.is_failure()


class TestSearchPlaylistsQueryHandler:
    """Test SearchPlaylistsQueryHandler."""

    def test_handle_found(self):
        """Test successful search."""
        playlist_ops = Mock()
        playlist_ops.get_all.return_value = [
            {
                "id": "p1",
                "name": "Rock Classics",
                "tracks": {"total": 50},
                "public": True,
                "external_urls": {"spotify": "https://spotify.com/p1"},
                "description": "Best rock songs",
            },
            {
                "id": "p2",
                "name": "Pop Hits",
                "tracks": {"total": 30},
                "public": False,
                "external_urls": {"spotify": "https://spotify.com/p2"},
                "description": "",
            },
        ]

        handler = SearchPlaylistsQueryHandler(playlist_ops)
        query = SearchPlaylistsQuery(search_term="rock")

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert response.total_count == 1
        assert response.playlists[0].name == "Rock Classics"

    def test_handle_case_insensitive(self):
        """Test that search is case insensitive."""
        playlist_ops = Mock()
        playlist_ops.get_all.return_value = [
            {
                "id": "p1",
                "name": "ROCK CLASSICS",
                "tracks": {"total": 50},
                "public": True,
                "external_urls": {"spotify": "https://spotify.com/p1"},
                "description": "",
            }
        ]

        handler = SearchPlaylistsQueryHandler(playlist_ops)
        query = SearchPlaylistsQuery(search_term="rock")

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert response.total_count == 1

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_ops = Mock()
        playlist_ops.get_all.side_effect = Exception("Error")

        handler = SearchPlaylistsQueryHandler(playlist_ops)
        query = SearchPlaylistsQuery(search_term="test")

        result = handler.handle(query)

        assert result.is_failure()


class TestGetPlaylistStatisticsQueryHandler:
    """Test GetPlaylistStatisticsQueryHandler."""

    def test_handle_success(self):
        """Test successful statistics calculation."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {"track": {"duration_ms": 180000, "explicit": False, "artists": [{"name": "A1"}]}},
                {"track": {"duration_ms": 200000, "explicit": True, "artists": [{"name": "A2"}]}},
                {"track": {"duration_ms": 220000, "explicit": False, "artists": [{"name": "A1"}]}},
            ]
        }

        handler = GetPlaylistStatisticsQueryHandler(playlist_reader)
        query = GetPlaylistStatisticsQuery(playlist_id="test_id")

        result = handler.handle(query)

        assert result.is_success()
        stats = result.unwrap()
        assert stats["total_tracks"] == 3
        assert stats["total_duration_ms"] == 600000
        assert stats["total_duration_minutes"] == 10
        assert stats["explicit_tracks"] == 1
        assert stats["unique_artists"] == 2
        assert stats["average_duration_ms"] == 200000

    def test_handle_empty_playlist(self):
        """Test statistics for empty playlist."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {"items": []}

        handler = GetPlaylistStatisticsQueryHandler(playlist_reader)
        query = GetPlaylistStatisticsQuery(playlist_id="test_id")

        result = handler.handle(query)

        assert result.is_success()
        stats = result.unwrap()
        assert stats["total_tracks"] == 0
        assert stats["average_duration_ms"] == 0

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.side_effect = Exception("Error")

        handler = GetPlaylistStatisticsQueryHandler(playlist_reader)
        query = GetPlaylistStatisticsQuery(playlist_id="test_id")

        result = handler.handle(query)

        assert result.is_failure()


class TestListRegionsQueryHandler:
    """Test ListRegionsQueryHandler."""

    def test_handle_success(self):
        """Test successful region listing."""
        chart_provider = Mock()
        chart_provider.get_available_regions.return_value = ["brazil", "us", "global"]

        handler = ListRegionsQueryHandler(chart_provider)
        query = ListRegionsQuery()

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert isinstance(response, RegionListResponse)
        assert len(response.regions) == 3
        assert all(isinstance(r, RegionInfo) for r in response.regions)

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        chart_provider = Mock()
        chart_provider.get_available_regions.side_effect = Exception("Error")

        handler = ListRegionsQueryHandler(chart_provider)
        query = ListRegionsQuery()

        result = handler.handle(query)

        assert result.is_failure()


class TestPreviewChartsQueryHandler:
    """Test PreviewChartsQueryHandler."""

    def test_handle_success(self):
        """Test successful chart preview."""
        chart_provider = Mock()
        tracks = [
            Track(id="t1", name="Song 1", artist="Artist 1", album="Album 1"),
            Track(id="t2", name="Song 2", artist="Artist 2", album="Album 2"),
        ]
        chart_provider.get_charts.return_value = Success(tracks)

        event_bus = EventBus()
        handler = PreviewChartsQueryHandler(chart_provider, event_bus)
        query = PreviewChartsQuery(region="brazil", limit=10)

        result = handler.handle(query)

        assert result.is_success()
        response = result.unwrap()
        assert isinstance(response, ChartPreviewResponse)
        assert response.region == "brazil"
        assert len(response.tracks) == 2
        assert response.total_tracks == 2

    def test_handle_chart_provider_failure(self):
        """Test handling when chart provider fails."""
        chart_provider = Mock()
        chart_provider.get_charts.return_value = Failure(Exception("Scraping failed"))

        handler = PreviewChartsQueryHandler(chart_provider)
        query = PreviewChartsQuery(region="brazil")

        result = handler.handle(query)

        assert result.is_failure()

    def test_handle_exception(self):
        """Test handling when an exception occurs."""
        chart_provider = Mock()
        chart_provider.get_charts.side_effect = Exception("Error")

        handler = PreviewChartsQueryHandler(chart_provider)
        query = PreviewChartsQuery(region="brazil")

        result = handler.handle(query)

        assert result.is_failure()
