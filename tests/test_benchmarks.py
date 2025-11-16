"""
Performance Benchmarks for Critical Paths

Uses pytest-benchmark to measure and track performance over time.
Run with: pytest tests/test_benchmarks.py --benchmark-only
Compare: pytest tests/test_benchmarks.py --benchmark-compare
"""

import pytest
from unittest.mock import Mock

from spotichart.core.models import Track, PlaylistMetadata
from spotichart.utils.result import Success, Failure
from spotichart.application.pydantic_dtos import (
    CreatePlaylistRequestV2,
    TrackV2,
    PlaylistStatisticsV2,
)
from spotichart.application.services import PlaylistApplicationService
from spotichart.core.playlist_manager import PlaylistManager
from spotichart.core.track_manager import TrackManager


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_tracks():
    """Generate mock tracks for benchmarking."""
    return [
        Track(
            id=f"track{i}",
            name=f"Song {i}",
            artist=f"Artist {i}",
            album=f"Album {i}"
        )
        for i in range(100)
    ]


@pytest.fixture
def mock_spotify_client():
    """Create a lightweight mock Spotify client."""
    client = Mock()
    client.me.return_value = {"id": "test_user"}
    client.user_playlist_create.return_value = {
        "id": "playlist123",
        "external_urls": {"spotify": "https://open.spotify.com/playlist/123"},
        "name": "Test"
    }
    client.current_user_playlists.return_value = {"items": [], "next": None, "total": 0}
    client.playlist_add_items.return_value = {"snapshot_id": "snap123"}
    return client


# ============================================================================
# MODEL BENCHMARKS
# ============================================================================


class TestModelBenchmarks:
    """Benchmark critical model operations."""

    def test_track_creation_performance(self, benchmark):
        """Benchmark: Creating Track instances."""
        def create_track():
            return Track(
                id="7ouMYWpwJ422jRcDASZB7P",
                name="Anti-Hero",
                artist="Taylor Swift",
                album="Midnights"
            )

        result = benchmark(create_track)
        assert result.id == "7ouMYWpwJ422jRcDASZB7P"

    def test_track_uri_generation_performance(self, benchmark):
        """Benchmark: Generating Track URIs."""
        track = Track(id="7ouMYWpwJ422jRcDASZB7P")

        def get_uri():
            return track.uri

        uri = benchmark(get_uri)
        assert uri.startswith("spotify:track:")

    def test_playlist_metadata_creation_performance(self, benchmark):
        """Benchmark: Creating PlaylistMetadata."""
        def create_metadata():
            return PlaylistMetadata(
                name="Top Songs",
                description="Best tracks of 2024",
                public=True
            )

        result = benchmark(create_metadata)
        assert result.name == "Top Songs"


# ============================================================================
# RESULT MONAD BENCHMARKS
# ============================================================================


class TestResultBenchmarks:
    """Benchmark Result monad operations."""

    def test_success_creation_performance(self, benchmark):
        """Benchmark: Creating Success results."""
        def create_success():
            return Success(42)

        result = benchmark(create_success)
        assert result.is_success()

    def test_failure_creation_performance(self, benchmark):
        """Benchmark: Creating Failure results."""
        def create_failure():
            return Failure("Error message")

        result = benchmark(create_failure)
        assert result.is_failure()

    def test_result_map_chain_performance(self, benchmark):
        """Benchmark: Chaining map operations."""
        def chain_maps():
            return (
                Success(10)
                .map(lambda x: x * 2)
                .map(lambda x: x + 5)
                .map(lambda x: x * 3)
            )

        result = benchmark(chain_maps)
        assert result.unwrap() == 75  # ((10*2)+5)*3


# ============================================================================
# PYDANTIC DTO BENCHMARKS
# ============================================================================


class TestPydanticBenchmarks:
    """Benchmark Pydantic DTO validation."""

    def test_create_playlist_request_validation(self, benchmark):
        """Benchmark: Validating CreatePlaylistRequestV2."""
        def create_and_validate():
            return CreatePlaylistRequestV2(
                name="Test Playlist",
                track_ids=[f"track{i}" for i in range(50)],
                public=True
            )

        result = benchmark(create_and_validate)
        assert len(result.track_ids) == 50

    def test_track_v2_validation(self, benchmark):
        """Benchmark: Validating TrackV2."""
        def create_and_validate():
            return TrackV2(
                id="7ouMYWpwJ422jRcDASZB7P",
                name="Anti-Hero",
                artist="Taylor Swift",
                popularity=95
            )

        result = benchmark(create_and_validate)
        assert result.popularity == 95

    def test_playlist_statistics_validation(self, benchmark):
        """Benchmark: Validating PlaylistStatisticsV2."""
        def create_and_validate():
            return PlaylistStatisticsV2(
                total_tracks=100,
                total_duration_ms=30000000,
                total_duration_minutes=500,
                explicit_tracks=10,
                unique_artists=75,
                average_duration_ms=300000,
            )

        result = benchmark(create_and_validate)
        assert result.total_tracks == 100


# ============================================================================
# BULK OPERATIONS BENCHMARKS
# ============================================================================


class TestBulkOperationsBenchmarks:
    """Benchmark bulk operations."""

    def test_bulk_track_creation(self, benchmark, mock_tracks):
        """Benchmark: Creating 100 tracks."""
        def create_bulk_tracks():
            return [
                Track(id=f"track{i}", name=f"Song {i}", artist=f"Artist {i}")
                for i in range(100)
            ]

        tracks = benchmark(create_bulk_tracks)
        assert len(tracks) == 100

    def test_bulk_track_uri_generation(self, benchmark, mock_tracks):
        """Benchmark: Generating URIs for 100 tracks."""
        def generate_uris():
            return [track.uri for track in mock_tracks]

        uris = benchmark(generate_uris)
        assert len(uris) == 100
        assert all(uri.startswith("spotify:track:") for uri in uris)

    def test_bulk_pydantic_validation(self, benchmark):
        """Benchmark: Validating 100 TrackV2 instances."""
        def validate_bulk():
            return [
                TrackV2(id=f"track{i}", popularity=i % 100)
                for i in range(100)
            ]

        tracks = benchmark(validate_bulk)
        assert len(tracks) == 100


# ============================================================================
# INTEGRATION BENCHMARKS
# ============================================================================


class TestIntegrationBenchmarks:
    """Benchmark integrated operations."""

    def test_playlist_application_service_creation(
        self, benchmark, mock_spotify_client, mock_tracks
    ):
        """Benchmark: Creating playlist through application service."""
        # Setup
        chart_provider = Mock()
        chart_provider.get_charts.return_value = Success(mock_tracks[:50])

        playlist_manager = PlaylistManager(mock_spotify_client)
        track_manager = TrackManager(mock_spotify_client)

        def create_playlist():
            app_service = PlaylistApplicationService(
                chart_provider=chart_provider,
                playlist_ops=playlist_manager,
                track_ops=track_manager,
            )
            return app_service.create_playlist_from_charts(
                region="brazil",
                limit=50,
                name="Benchmark Test",
                public=False,
                update_mode="new"
            )

        result = benchmark(create_playlist)
        assert result.is_success()


# ============================================================================
# STRESS TESTS
# ============================================================================


class TestStressBenchmarks:
    """Stress tests for edge cases."""

    def test_large_playlist_1000_tracks(self, benchmark):
        """Stress test: Creating playlist request with 1000 tracks."""
        def create_large_request():
            return CreatePlaylistRequestV2(
                name="Large Playlist",
                track_ids=[f"track{i}" for i in range(1000)]
            )

        result = benchmark(create_large_request)
        assert len(result.track_ids) == 1000

    def test_deep_result_chain(self, benchmark):
        """Stress test: Deep chain of Result.map operations."""
        def deep_chain():
            result = Success(1)
            for _ in range(50):
                result = result.map(lambda x: x + 1)
            return result

        result = benchmark(deep_chain)
        assert result.unwrap() == 51


# ============================================================================
# BENCHMARK CONFIGURATIONS
# ============================================================================


# Run with: pytest tests/test_benchmarks.py --benchmark-only -v
# Compare: pytest tests/test_benchmarks.py --benchmark-compare
# Save baseline: pytest tests/test_benchmarks.py --benchmark-save=baseline
# Auto-save: pytest tests/test_benchmarks.py --benchmark-autosave
