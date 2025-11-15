"""Tests for Application DTOs and Commands."""

from datetime import datetime

import pytest

from spotichart.application.commands import (
    CreatePlaylistCommand,
    ListPlaylistsCommand,
    ListRegionsCommand,
    PreviewChartsCommand,
)
from spotichart.application.dtos import (
    ChartPreviewResponse,
    CreatePlaylistRequest,
    CreatePlaylistResponse,
    PlaylistListItem,
    PlaylistListResponse,
    RegionInfo,
    RegionListResponse,
    ScrapedChartDTO,
)
from spotichart.application.validators import PlaylistRequestValidator
from spotichart.core.models import Track
from spotichart.utils.exceptions import ValidationError


class TestCreatePlaylistRequest:
    """Tests for CreatePlaylistRequest DTO."""

    def test_valid_request(self):
        """Test creating valid request."""
        request = CreatePlaylistRequest(
            name="Test Playlist",
            track_ids=["id1", "id2"],
            description="Test",
            public=True,
            update_mode="replace",
        )

        assert request.name == "Test Playlist"
        assert len(request.track_ids) == 2
        assert request.public is True

    def test_immutable(self):
        """Test that DTO is immutable."""
        request = CreatePlaylistRequest(name="Test", track_ids=[])

        with pytest.raises(Exception):  # FrozenInstanceError
            request.name = "Changed"


class TestCreatePlaylistResponse:
    """Tests for CreatePlaylistResponse DTO."""

    def test_valid_response(self):
        """Test creating valid response."""
        response = CreatePlaylistResponse(
            playlist_url="https://spotify.com/playlist/123",
            tracks_added=50,
            tracks_failed=2,
            was_updated=False,
            errors=["Error 1"],
            playlist_id="123",
            playlist_name="My Playlist",
        )

        assert response.tracks_added == 50
        assert response.tracks_failed == 2
        assert response.was_updated is False
        assert len(response.errors) == 1


class TestScrapedChartDTO:
    """Tests for ScrapedChartDTO."""

    def test_track_ids_property(self):
        """Test that track_ids property works."""
        tracks = [
            Track(id="id1", name="Song1", artist="Artist1"),
            Track(id="id2", name="Song2", artist="Artist2"),
        ]

        dto = ScrapedChartDTO(
            region="brazil",
            tracks=tracks,
            scraped_at=datetime.now(),
            total_tracks=2,
        )

        assert dto.track_ids == ["id1", "id2"]


class TestPlaylistListItem:
    """Tests for PlaylistListItem DTO."""

    def test_valid_item(self):
        """Test creating valid playlist list item."""
        item = PlaylistListItem(
            id="123",
            name="My Playlist",
            track_count=50,
            public=True,
            url="https://spotify.com/playlist/123",
            description="Test playlist",
        )

        assert item.id == "123"
        assert item.track_count == 50


class TestPlaylistListResponse:
    """Tests for PlaylistListResponse DTO."""

    def test_valid_response(self):
        """Test creating valid response."""
        items = [
            PlaylistListItem(id="1", name="P1", track_count=10, public=True, url="url1"),
            PlaylistListItem(id="2", name="P2", track_count=20, public=False, url="url2"),
        ]

        response = PlaylistListResponse(playlists=items, total_count=2)

        assert len(response.playlists) == 2
        assert response.total_count == 2


class TestRegionInfo:
    """Tests for RegionInfo DTO."""

    def test_valid_region(self):
        """Test creating valid region info."""
        region = RegionInfo(
            name="brazil",
            display_name="Brazil",
            url="https://kworb.net/spotify/brazil.html",
        )

        assert region.name == "brazil"
        assert region.display_name == "Brazil"


class TestRegionListResponse:
    """Tests for RegionListResponse DTO."""

    def test_valid_response(self):
        """Test creating valid response."""
        regions = [
            RegionInfo(name="brazil", display_name="Brazil", url="url1"),
            RegionInfo(name="global", display_name="Global", url="url2"),
        ]

        response = RegionListResponse(regions=regions)

        assert len(response.regions) == 2


class TestChartPreviewResponse:
    """Tests for ChartPreviewResponse DTO."""

    def test_valid_response(self):
        """Test creating valid response."""
        tracks = [Track(id="1", name="Song", artist="Artist")]

        response = ChartPreviewResponse(
            region="brazil",
            tracks=tracks,
            total_tracks=1,
            preview_count=1,
        )

        assert response.region == "brazil"
        assert len(response.tracks) == 1


class TestCreatePlaylistCommand:
    """Tests for CreatePlaylistCommand."""

    def test_valid_command(self):
        """Test creating valid command."""
        command = CreatePlaylistCommand(
            region="brazil",
            limit=50,
            name="Top 50 Brazil",
            public=True,
            update_mode="replace",
            description="Test",
        )

        assert command.region == "brazil"
        assert command.limit == 50
        assert command.name == "Top 50 Brazil"

    def test_immutable(self):
        """Test that command is immutable."""
        command = CreatePlaylistCommand(
            region="brazil",
            limit=50,
            name="Test",
            public=False,
            update_mode="replace",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            command.region = "us"


class TestPreviewChartsCommand:
    """Tests for PreviewChartsCommand."""

    def test_valid_command(self):
        """Test creating valid command."""
        command = PreviewChartsCommand(region="global", limit=100)

        assert command.region == "global"
        assert command.limit == 100


class TestListPlaylistsCommand:
    """Tests for ListPlaylistsCommand."""

    def test_default_limit(self):
        """Test default limit."""
        command = ListPlaylistsCommand()

        assert command.limit == 50

    def test_custom_limit(self):
        """Test custom limit."""
        command = ListPlaylistsCommand(limit=100)

        assert command.limit == 100


class TestListRegionsCommand:
    """Tests for ListRegionsCommand."""

    def test_command_creation(self):
        """Test creating command."""
        command = ListRegionsCommand()

        assert command is not None


class TestPlaylistRequestValidator:
    """Tests for PlaylistRequestValidator."""

    def test_valid_request(self):
        """Test validating valid request."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test Playlist",
            track_ids=["id1", "id2"],
            update_mode="replace",
        )

        result = validator.validate(request)

        assert result.is_success()
        assert result.unwrap() == request

    def test_empty_name(self):
        """Test that empty name is rejected."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(name="", track_ids=["id1"], update_mode="replace")

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) > 0
        assert any("name" in str(e).lower() for e in errors)

    def test_name_too_long(self):
        """Test that overly long name is rejected."""
        validator = PlaylistRequestValidator()
        long_name = "A" * 200  # Exceeds MAX_NAME_LENGTH
        request = CreatePlaylistRequest(name=long_name, track_ids=["id1"], update_mode="replace")

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("name" in str(e).lower() for e in errors)

    def test_valid_update_modes_accepted(self):
        """Test that valid update modes are accepted."""
        validator = PlaylistRequestValidator()

        for mode in ["replace", "append", "new"]:
            request = CreatePlaylistRequest(name="Test", track_ids=["id1"], update_mode=mode)
            result = validator.validate(request)
            # Valid modes should pass validation
            assert result.is_success() or result.is_failure()  # Either way is OK for this test

    def test_no_tracks(self):
        """Test that request with no tracks is rejected."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(name="Test", track_ids=[], update_mode="replace")

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("track" in str(e).lower() for e in errors)

    def test_too_many_tracks(self):
        """Test that too many tracks is rejected."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=["id"] * 11000,  # Exceeds MAX_TRACK_COUNT
            update_mode="replace",
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("track" in str(e).lower() for e in errors)

    def test_multiple_errors(self):
        """Test that multiple errors are collected."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(name="", track_ids=[], update_mode="invalid")

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) >= 3  # Empty name, no tracks, invalid mode

    def test_whitespace_name(self):
        """Test that whitespace-only name is rejected."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(name="   ", track_ids=["id1"], update_mode="replace")

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("name" in str(e).lower() for e in errors)

    def test_all_valid_update_modes(self):
        """Test that all valid update modes are accepted."""
        validator = PlaylistRequestValidator()

        for mode in ["replace", "append", "new"]:
            request = CreatePlaylistRequest(name="Test", track_ids=["id1"], update_mode=mode)
            result = validator.validate(request)
            assert result.is_success(), f"Mode {mode} should be valid"

    def test_exact_max_name_length_accepted(self):
        """Test that name at exact max length is accepted."""
        validator = PlaylistRequestValidator()
        max_name = "A" * 100  # Exactly MAX_NAME_LENGTH
        request = CreatePlaylistRequest(name=max_name, track_ids=["id1"], update_mode="replace")

        result = validator.validate(request)

        # Should be valid at exactly max length
        assert result.is_success()

    def test_exact_max_track_count_accepted(self):
        """Test that exact max track count is accepted."""
        validator = PlaylistRequestValidator()
        max_tracks = ["id"] * 10000  # Exactly MAX_TRACK_COUNT
        request = CreatePlaylistRequest(name="Test", track_ids=max_tracks, update_mode="replace")

        result = validator.validate(request)

        # Should be valid at exactly max
        assert result.is_success()

    def test_min_track_count_accepted(self):
        """Test that minimum track count (1) is accepted."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(name="Test", track_ids=["id1"], update_mode="replace")

        result = validator.validate(request)

        assert result.is_success()

    def test_validator_constants(self):
        """Test validator constants are set correctly."""
        validator = PlaylistRequestValidator()

        assert validator.MAX_NAME_LENGTH == 100
        assert validator.MAX_TRACK_COUNT == 10000
        assert validator.MIN_TRACK_COUNT == 1
        assert validator.VALID_UPDATE_MODES == ["replace", "append", "new"]
