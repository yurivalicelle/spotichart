"""
Tests for Value Objects (Domain Models)
"""

import pytest

from spotichart.core.models import ChartEntry, PlaylistMetadata, Track


class TestTrack:
    """Test Track value object."""

    def test_track_creation(self):
        """Track should be created with id."""
        track = Track(id="track123")
        assert track.id == "track123"
        assert track.name is None
        assert track.artist is None

    def test_track_with_metadata(self):
        """Track can have name and artist."""
        track = Track(id="track123", name="Song Name", artist="Artist Name")
        assert track.name == "Song Name"
        assert track.artist == "Artist Name"

    def test_track_uri(self):
        """Track should generate Spotify URI."""
        track = Track(id="track123")
        assert track.uri == "spotify:track:track123"

    def test_track_str_with_metadata(self):
        """Track string should show artist and name."""
        track = Track(id="track123", name="Song", artist="Artist")
        assert str(track) == "Artist - Song"

    def test_track_str_without_metadata(self):
        """Track string should show id if no metadata."""
        track = Track(id="track123")
        assert str(track) == "track123"

    def test_track_immutable(self):
        """Track should be immutable."""
        track = Track(id="track123")
        with pytest.raises(AttributeError):
            track.id = "new_id"

    def test_track_with_album(self):
        """Track can have album."""
        track = Track(id="track123", name="Song", artist="Artist", album="Album")
        assert track.album == "Album"


class TestPlaylistMetadata:
    """Test PlaylistMetadata value object."""

    def test_playlist_creation(self):
        """PlaylistMetadata should be created with name and description."""
        metadata = PlaylistMetadata(name="My Playlist", description="My Description")
        assert metadata.name == "My Playlist"
        assert metadata.description == "My Description"
        assert metadata.public is False
        assert metadata.collaborative is False

    def test_playlist_public(self):
        """PlaylistMetadata can be public."""
        metadata = PlaylistMetadata(name="Playlist", description="Desc", public=True)
        assert metadata.public is True

    def test_playlist_collaborative(self):
        """PlaylistMetadata can be collaborative."""
        metadata = PlaylistMetadata(
            name="Playlist", description="Desc", collaborative=True
        )
        assert metadata.collaborative is True

    def test_playlist_immutable(self):
        """PlaylistMetadata should be immutable."""
        metadata = PlaylistMetadata(name="Playlist", description="Desc")
        with pytest.raises(AttributeError):
            metadata.name = "New Name"

    def test_with_description(self):
        """with_description should create new instance."""
        metadata = PlaylistMetadata(name="Playlist", description="Old")
        new_metadata = metadata.with_description("New Description")

        assert metadata.description == "Old"
        assert new_metadata.description == "New Description"
        assert new_metadata.name == "Playlist"
        assert new_metadata.public == metadata.public

    def test_with_visibility(self):
        """with_visibility should create new instance."""
        metadata = PlaylistMetadata(name="Playlist", description="Desc", public=False)
        new_metadata = metadata.with_visibility(public=True)

        assert metadata.public is False
        assert new_metadata.public is True
        assert new_metadata.name == "Playlist"
        assert new_metadata.description == "Desc"


class TestChartEntry:
    """Test ChartEntry value object."""

    def test_chart_entry_creation(self):
        """ChartEntry should be created with track_id, position, region."""
        entry = ChartEntry(track_id="track123", position=1, region="brazil")
        assert entry.track_id == "track123"
        assert entry.position == 1
        assert entry.region == "brazil"

    def test_chart_entry_immutable(self):
        """ChartEntry should be immutable."""
        entry = ChartEntry(track_id="track123", position=1, region="brazil")
        with pytest.raises(AttributeError):
            entry.position = 2

    def test_to_track(self):
        """ChartEntry should convert to Track."""
        entry = ChartEntry(track_id="track123", position=1, region="brazil")
        track = entry.to_track()

        assert isinstance(track, Track)
        assert track.id == "track123"
        assert track.name is None
        assert track.artist is None
