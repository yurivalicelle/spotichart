"""
Tests for Pydantic DTOs

Tests validation, immutability, and edge cases.
"""

import pytest
from pydantic import ValidationError

from spotichart.application.pydantic_dtos import (
    ApplicationConfigV2,
    ChartPreviewRequestV2,
    CreatePlaylistRequestV2,
    CreatePlaylistResponseV2,
    PlaylistStatisticsV2,
    SearchPlaylistsRequestV2,
    SpotifyCredentialsV2,
    TrackV2,
    validate_and_convert,
)


class TestCreatePlaylistRequestV2:
    """Test CreatePlaylistRequestV2 validation."""

    def test_valid_request(self):
        """Test creating valid request."""
        request = CreatePlaylistRequestV2(
            name="Test Playlist",
            track_ids=["track1", "track2", "track3"],
            description="Test description",
            public=True,
            update_mode="replace",
            region="brazil",
        )

        assert request.name == "Test Playlist"
        assert len(request.track_ids) == 3
        assert request.public is True
        assert request.update_mode == "replace"

    def test_minimal_valid_request(self):
        """Test minimal valid request with defaults."""
        request = CreatePlaylistRequestV2(name="Test", track_ids=["track1"])

        assert request.name == "Test"
        assert request.description == ""
        assert request.public is False
        assert request.update_mode == "replace"

    def test_name_too_short(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="", track_ids=["track1"])

        errors = exc_info.value.errors()
        assert any("name" in str(e["loc"]) for e in errors)

    def test_name_too_long(self):
        """Test validation fails for name too long."""
        long_name = "A" * 101

        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name=long_name, track_ids=["track1"])

        errors = exc_info.value.errors()
        assert any("name" in str(e["loc"]) for e in errors)

    def test_name_whitespace_only(self):
        """Test validation fails for whitespace-only name."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="   ", track_ids=["track1"])

        errors = exc_info.value.errors()
        assert "name" in str(errors)

    def test_name_auto_stripped(self):
        """Test that name is auto-stripped."""
        request = CreatePlaylistRequestV2(name="  Test  ", track_ids=["track1"])

        assert request.name == "Test"

    def test_no_track_ids(self):
        """Test validation fails when no track IDs."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="Test", track_ids=[])

        errors = exc_info.value.errors()
        assert any("track_ids" in str(e["loc"]) for e in errors)

    def test_too_many_tracks(self):
        """Test validation fails for too many tracks."""
        too_many_tracks = ["track"] * 10001

        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="Test", track_ids=too_many_tracks)

        errors = exc_info.value.errors()
        assert any("track_ids" in str(e["loc"]) for e in errors)

    def test_empty_track_id(self):
        """Test validation fails for empty track ID."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="Test", track_ids=["track1", "", "track3"])

        errors = exc_info.value.errors()
        assert "track_ids" in str(errors).lower()

    def test_invalid_update_mode(self):
        """Test validation fails for invalid update mode."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(name="Test", track_ids=["track1"], update_mode="invalid")

        errors = exc_info.value.errors()
        assert "update_mode" in str(errors).lower()

    def test_all_valid_update_modes(self):
        """Test all valid update modes."""
        for mode in ["replace", "append", "new"]:
            request = CreatePlaylistRequestV2(name="Test", track_ids=["track1"], update_mode=mode)
            assert request.update_mode == mode

    def test_immutability(self):
        """Test that request is immutable."""
        request = CreatePlaylistRequestV2(name="Test", track_ids=["track1"])

        with pytest.raises(ValidationError):
            request.name = "New Name"  # type: ignore

    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistRequestV2(
                name="Test", track_ids=["track1"], extra_field="not_allowed"  # type: ignore
            )

        errors = exc_info.value.errors()
        assert any("extra_field" in str(e) for e in errors)

    def test_type_coercion(self):
        """Test that types are coerced when possible."""
        # Public should be coerced to bool
        request = CreatePlaylistRequestV2(name="Test", track_ids=["track1"], public=1)  # type: ignore

        assert request.public is True


class TestCreatePlaylistResponseV2:
    """Test CreatePlaylistResponseV2 validation."""

    def test_valid_response(self):
        """Test creating valid response."""
        response = CreatePlaylistResponseV2(
            playlist_url="https://open.spotify.com/playlist/abc123",
            playlist_id="abc123",
            playlist_name="Test Playlist",
            tracks_added=50,
            tracks_failed=0,
            was_updated=False,
        )

        assert response.playlist_id == "abc123"
        assert response.tracks_added == 50
        assert response.tracks_failed == 0
        assert len(response.errors) == 0

    def test_negative_tracks_added(self):
        """Test validation fails for negative tracks_added."""
        with pytest.raises(ValidationError):
            CreatePlaylistResponseV2(
                playlist_url="https://open.spotify.com/playlist/abc123",
                playlist_id="abc123",
                playlist_name="Test",
                tracks_added=-1,  # Invalid
                tracks_failed=0,
                was_updated=False,
            )

    def test_tracks_failed_without_errors(self):
        """Test validation fails when tracks_failed > 0 but no errors."""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlaylistResponseV2(
                playlist_url="https://open.spotify.com/playlist/abc123",
                playlist_id="abc123",
                playlist_name="Test",
                tracks_added=40,
                tracks_failed=10,  # > 0
                was_updated=False,
                errors=[],  # Empty!
            )

        assert "errors" in str(exc_info.value).lower()

    def test_with_errors(self):
        """Test response with errors."""
        response = CreatePlaylistResponseV2(
            playlist_url="https://open.spotify.com/playlist/abc123",
            playlist_id="abc123",
            playlist_name="Test",
            tracks_added=40,
            tracks_failed=10,
            was_updated=False,
            errors=["Error 1", "Error 2"],
        )

        assert len(response.errors) == 2
        assert response.tracks_failed == 10

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        response = CreatePlaylistResponseV2(
            playlist_url="https://open.spotify.com/playlist/abc123",
            playlist_id="abc123",
            playlist_name="Test",
            tracks_added=50,
            tracks_failed=0,
            was_updated=False,
        )

        assert response.created_at is not None


class TestPlaylistStatisticsV2:
    """Test PlaylistStatisticsV2 validation."""

    def test_valid_statistics(self):
        """Test creating valid statistics."""
        stats = PlaylistStatisticsV2(
            total_tracks=100,
            total_duration_ms=30000000,
            total_duration_minutes=500,
            explicit_tracks=10,
            unique_artists=50,
            average_duration_ms=300000,
        )

        assert stats.total_tracks == 100
        assert stats.explicit_tracks == 10

    def test_negative_values(self):
        """Test validation fails for negative values."""
        with pytest.raises(ValidationError):
            PlaylistStatisticsV2(
                total_tracks=-1,  # Invalid
                total_duration_ms=1000,
                total_duration_minutes=1,
                explicit_tracks=0,
                unique_artists=0,
                average_duration_ms=0,
            )

    def test_explicit_tracks_exceed_total(self):
        """Test validation fails when explicit > total."""
        with pytest.raises(ValidationError) as exc_info:
            PlaylistStatisticsV2(
                total_tracks=10,
                total_duration_ms=1000,
                total_duration_minutes=1,
                explicit_tracks=20,  # > total_tracks!
                unique_artists=5,
                average_duration_ms=100,
            )

        assert "explicit_tracks" in str(exc_info.value).lower()

    def test_zero_average_duration_with_tracks(self):
        """Test validation fails when avg duration is 0 with tracks."""
        with pytest.raises(ValidationError) as exc_info:
            PlaylistStatisticsV2(
                total_tracks=10,  # > 0
                total_duration_ms=1000,
                total_duration_minutes=1,
                explicit_tracks=5,
                unique_artists=5,
                average_duration_ms=0,  # Should be > 0!
            )

        assert "average_duration_ms" in str(exc_info.value).lower()


class TestTrackV2:
    """Test TrackV2 validation."""

    def test_valid_track(self):
        """Test creating valid track."""
        track = TrackV2(
            id="7ouMYWpwJ422jRcDASZB7P",
            name="Song Title",
            artist="Artist Name",
            album="Album Title",
            duration_ms=180000,
            popularity=85,
            explicit=False,
        )

        assert track.id == "7ouMYWpwJ422jRcDASZB7P"
        assert track.name == "Song Title"
        assert track.uri == "spotify:track:7ouMYWpwJ422jRcDASZB7P"

    def test_minimal_track(self):
        """Test track with only ID."""
        track = TrackV2(id="track123")

        assert track.id == "track123"
        assert track.name is None
        assert track.uri == "spotify:track:track123"

    def test_empty_id(self):
        """Test validation fails for empty ID."""
        with pytest.raises(ValidationError):
            TrackV2(id="")

    def test_negative_duration(self):
        """Test validation fails for negative duration."""
        with pytest.raises(ValidationError):
            TrackV2(id="track123", duration_ms=-1)

    def test_invalid_popularity(self):
        """Test validation fails for popularity > 100."""
        with pytest.raises(ValidationError):
            TrackV2(id="track123", popularity=101)

    def test_string_representation(self):
        """Test string representation."""
        track = TrackV2(id="track123", name="Song", artist="Artist")
        assert str(track) == "Artist - Song"

        track_no_metadata = TrackV2(id="track123")
        assert str(track_no_metadata) == "track123"


class TestSearchPlaylistsRequestV2:
    """Test SearchPlaylistsRequestV2 validation."""

    def test_valid_request(self):
        """Test valid search request."""
        request = SearchPlaylistsRequestV2(search_term="rock", limit=10, include_private=False)

        assert request.search_term == "rock"
        assert request.limit == 10
        assert request.include_private is False

    def test_empty_search_term(self):
        """Test validation fails for empty search term."""
        with pytest.raises(ValidationError):
            SearchPlaylistsRequestV2(search_term="")

    def test_search_term_auto_lowercased(self):
        """Test search term is lowercased."""
        request = SearchPlaylistsRequestV2(search_term="ROCK")

        assert request.search_term == "rock"

    def test_limit_bounds(self):
        """Test limit bounds validation."""
        # Too low
        with pytest.raises(ValidationError):
            SearchPlaylistsRequestV2(search_term="rock", limit=0)

        # Too high
        with pytest.raises(ValidationError):
            SearchPlaylistsRequestV2(search_term="rock", limit=101)

        # Valid bounds
        SearchPlaylistsRequestV2(search_term="rock", limit=1)
        SearchPlaylistsRequestV2(search_term="rock", limit=100)


class TestSpotifyCredentialsV2:
    """Test SpotifyCredentialsV2 validation."""

    def test_valid_credentials(self):
        """Test valid credentials."""
        creds = SpotifyCredentialsV2(
            client_id="a" * 32, client_secret="b" * 32, redirect_uri="http://localhost:8888/callback"
        )

        assert len(creds.client_id) == 32
        assert len(creds.client_secret) == 32

    def test_invalid_length(self):
        """Test validation fails for wrong length."""
        with pytest.raises(ValidationError):
            SpotifyCredentialsV2(client_id="too_short", client_secret="a" * 32)

    def test_placeholder_rejected(self):
        """Test placeholder values are rejected."""
        with pytest.raises(ValidationError):
            SpotifyCredentialsV2(
                client_id="your_client_id_here" + " " * 10, client_secret="a" * 32
            )

    def test_invalid_redirect_uri(self):
        """Test invalid redirect URI."""
        with pytest.raises(ValidationError):
            SpotifyCredentialsV2(
                client_id="a" * 32, client_secret="b" * 32, redirect_uri="not_a_url"
            )


class TestApplicationConfigV2:
    """Test ApplicationConfigV2 validation."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = ApplicationConfigV2(
            log_level="DEBUG",
            cache_ttl_seconds=600,
            max_retries=5,
            request_timeout=60,
            enable_metrics=True,
            enable_caching=False,
        )

        assert config.log_level == "DEBUG"
        assert config.max_retries == 5

    def test_default_config(self):
        """Test default configuration."""
        config = ApplicationConfigV2()

        assert config.log_level == "INFO"
        assert config.cache_ttl_seconds == 300
        assert config.max_retries == 3

    def test_invalid_log_level(self):
        """Test invalid log level."""
        with pytest.raises(ValidationError):
            ApplicationConfigV2(log_level="INVALID")

    def test_cache_ttl_bounds(self):
        """Test cache TTL bounds."""
        # Too low
        with pytest.raises(ValidationError):
            ApplicationConfigV2(cache_ttl_seconds=-1)

        # Too high
        with pytest.raises(ValidationError):
            ApplicationConfigV2(cache_ttl_seconds=3601)

    def test_max_retries_bounds(self):
        """Test max retries bounds."""
        with pytest.raises(ValidationError):
            ApplicationConfigV2(max_retries=11)


class TestChartPreviewRequestV2:
    """Test ChartPreviewRequestV2 validation."""

    def test_valid_request(self):
        """Test valid preview request."""
        request = ChartPreviewRequestV2(region="brazil", limit=100)

        assert request.region == "brazil"
        assert request.limit == 100

    def test_region_auto_lowercased(self):
        """Test region is lowercased."""
        request = ChartPreviewRequestV2(region="BRAZIL")

        assert request.region == "brazil"

    def test_empty_region(self):
        """Test empty region fails."""
        with pytest.raises(ValidationError):
            ChartPreviewRequestV2(region="")

    def test_limit_bounds(self):
        """Test limit bounds."""
        # Valid
        ChartPreviewRequestV2(region="brazil", limit=1)
        ChartPreviewRequestV2(region="brazil", limit=1000)

        # Too low
        with pytest.raises(ValidationError):
            ChartPreviewRequestV2(region="brazil", limit=0)

        # Too high
        with pytest.raises(ValidationError):
            ChartPreviewRequestV2(region="brazil", limit=1001)


class TestHelperFunctions:
    """Test helper functions."""

    def test_validate_and_convert_success(self):
        """Test successful validation and conversion."""
        data = {"name": "Test", "track_ids": ["track1"]}

        result = validate_and_convert(data, CreatePlaylistRequestV2)

        assert isinstance(result, CreatePlaylistRequestV2)
        assert result.name == "Test"

    def test_validate_and_convert_failure(self):
        """Test validation failure."""
        data = {"name": "", "track_ids": []}  # Invalid

        with pytest.raises(ValidationError):
            validate_and_convert(data, CreatePlaylistRequestV2)
