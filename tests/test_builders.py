"""Tests for Builder Pattern."""

import pytest

from spotichart.application.dtos import CreatePlaylistRequest
from spotichart.core.models import Track
from spotichart.domain.builders import PlaylistBuilder, TrackCollectionBuilder
from spotichart.domain.pipelines import LimitTracksStep, Pipeline, RemoveDuplicatesStep
from spotichart.domain.specifications import (
    AlwaysFalseSpecification,
    TrackHasMetadataSpecification,
)


class TestPlaylistBuilder:
    """Tests for PlaylistBuilder."""

    def test_build_minimal_playlist(self):
        """Test building playlist with minimal required fields."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test Playlist").build()

        assert isinstance(request, CreatePlaylistRequest)
        assert request.name == "Test Playlist"
        assert request.track_ids == []
        assert request.description == ""
        assert request.public is False
        assert request.update_mode == "replace"

    def test_build_without_name_raises_error(self):
        """Test that building without name raises ValueError."""
        builder = PlaylistBuilder()

        with pytest.raises(ValueError, match="Playlist name is required"):
            builder.build()

    def test_with_description(self):
        """Test setting description."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").with_description("My playlist").build()

        assert request.description == "My playlist"

    def test_with_public(self):
        """Test setting public visibility."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").with_public(True).build()

        assert request.public is True

    def test_with_update_mode(self):
        """Test setting update mode."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").with_update_mode("append").build()

        assert request.update_mode == "append"

    def test_with_region(self):
        """Test setting region."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").with_region("brazil").build()

        assert request.region == "brazil"

    def test_add_track_id(self):
        """Test adding a single track ID."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").add_track_id("track123").build()

        assert len(request.track_ids) == 1
        assert request.track_ids[0] == "track123"

    def test_add_track_ids(self):
        """Test adding multiple track IDs."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").add_track_ids(["track1", "track2", "track3"]).build()

        assert len(request.track_ids) == 3

    def test_add_duplicate_track_ids(self):
        """Test that duplicate track IDs are not added."""
        builder = PlaylistBuilder()
        request = builder.with_name("Test").add_track_id("track1").add_track_id("track1").build()

        assert len(request.track_ids) == 1

    def test_add_track(self):
        """Test adding a single track."""
        builder = PlaylistBuilder()
        track = Track(id="track1", name="Song", artist="Artist")

        request = builder.with_name("Test").add_track(track).build()

        assert len(request.track_ids) == 1
        assert request.track_ids[0] == "track1"

    def test_add_tracks(self):
        """Test adding multiple tracks."""
        builder = PlaylistBuilder()
        tracks = [
            Track(id="track1", name="Song1", artist="Artist"),
            Track(id="track2", name="Song2", artist="Artist"),
        ]

        request = builder.with_name("Test").add_tracks(tracks).build()

        assert len(request.track_ids) == 2

    def test_add_track_without_id_skipped(self):
        """Test that tracks without ID are skipped."""
        builder = PlaylistBuilder()
        track = Track(id=None, name="Song", artist="Artist")

        request = builder.with_name("Test").add_track(track).build()

        assert len(request.track_ids) == 0

    def test_with_filter(self):
        """Test applying a filter specification."""
        builder = PlaylistBuilder()
        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id="2", name=None, artist="Artist"),
        ]

        request = (
            builder.with_name("Test")
            .add_tracks(tracks)
            .with_filter(TrackHasMetadataSpecification())
            .build()
        )

        # Only track with metadata should be included
        assert len(request.track_ids) == 1
        assert request.track_ids[0] == "1"

    def test_with_pipeline(self):
        """Test applying a processing pipeline."""
        builder = PlaylistBuilder()
        pipeline = Pipeline().add_step(RemoveDuplicatesStep()).add_step(LimitTracksStep(2))

        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="1", name="Song1 Dup", artist="Artist"),
            Track(id="3", name="Song3", artist="Artist"),
        ]

        request = builder.with_name("Test").add_tracks(tracks).with_pipeline(pipeline).build()

        # Should remove duplicate and limit to 2
        assert len(request.track_ids) == 2

    def test_add_pipeline_step(self):
        """Test adding individual pipeline steps."""
        builder = PlaylistBuilder()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="3", name="Song3", artist="Artist"),
        ]

        request = (
            builder.with_name("Test")
            .add_tracks(tracks)
            .add_pipeline_step(LimitTracksStep(2))
            .build()
        )

        assert len(request.track_ids) == 2

    def test_method_chaining(self):
        """Test fluent API with method chaining."""
        request = (
            PlaylistBuilder()
            .with_name("Chained Playlist")
            .with_description("Created with chaining")
            .with_public(True)
            .with_update_mode("append")
            .with_region("global")
            .add_track_id("track1")
            .add_track_id("track2")
            .build()
        )

        assert request.name == "Chained Playlist"
        assert request.description == "Created with chaining"
        assert request.public is True
        assert request.update_mode == "append"
        assert request.region == "global"
        assert len(request.track_ids) == 2

    def test_reset(self):
        """Test resetting builder to initial state."""
        builder = (
            PlaylistBuilder().with_name("Test").with_description("Desc").add_track_id("track1")
        )

        builder.reset()

        with pytest.raises(ValueError):
            builder.build()

    def test_combine_track_ids_and_tracks(self):
        """Test combining explicitly added IDs with track objects."""
        builder = PlaylistBuilder()
        track = Track(id="track2", name="Song", artist="Artist")

        request = builder.with_name("Test").add_track_id("track1").add_track(track).build()

        assert len(request.track_ids) == 2
        assert "track1" in request.track_ids
        assert "track2" in request.track_ids

    def test_filter_removes_tracks(self):
        """Test that filter that rejects all tracks works."""
        builder = PlaylistBuilder()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        request = (
            builder.with_name("Test")
            .add_tracks(tracks)
            .with_filter(AlwaysFalseSpecification())
            .build()
        )

        assert len(request.track_ids) == 0


class TestTrackCollectionBuilder:
    """Tests for TrackCollectionBuilder."""

    def test_build_empty_collection(self):
        """Test building empty track collection."""
        builder = TrackCollectionBuilder()
        result = builder.build()

        assert result == []

    def test_add_single_track(self):
        """Test adding a single track."""
        builder = TrackCollectionBuilder()
        track = Track(id="1", name="Song", artist="Artist")

        result = builder.add_track(track).build()

        assert len(result) == 1
        assert result[0] == track

    def test_add_multiple_tracks(self):
        """Test adding multiple tracks."""
        builder = TrackCollectionBuilder()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = builder.add_tracks(tracks).build()

        assert len(result) == 2

    def test_with_filter(self):
        """Test filtering tracks."""
        builder = TrackCollectionBuilder()
        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id="2", name=None, artist="Artist"),
        ]

        result = builder.add_tracks(tracks).with_filter(TrackHasMetadataSpecification()).build()

        assert len(result) == 1
        assert result[0].id == "1"

    def test_with_pipeline(self):
        """Test applying pipeline."""
        builder = TrackCollectionBuilder()
        pipeline = Pipeline().add_step(RemoveDuplicatesStep())

        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id="1", name="Song Dup", artist="Artist"),
        ]

        result = builder.add_tracks(tracks).with_pipeline(pipeline).build()

        assert len(result) == 1

    def test_with_limit(self):
        """Test limiting tracks."""
        builder = TrackCollectionBuilder()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="3", name="Song3", artist="Artist"),
        ]

        result = builder.add_tracks(tracks).with_limit(2).build()

        assert len(result) == 2

    def test_filter_pipeline_and_limit(self):
        """Test combining filter, pipeline, and limit."""
        builder = TrackCollectionBuilder()
        pipeline = Pipeline().add_step(RemoveDuplicatesStep())

        tracks = [
            Track(id="1", name="Song1", artist="Artist1"),
            Track(id="2", name="Song2", artist="Artist2"),
            Track(id="1", name="Song1 Dup", artist="Artist1"),  # Duplicate
            Track(id="3", name=None, artist="Artist3"),  # No metadata
            Track(id="4", name="Song4", artist="Artist4"),
        ]

        result = (
            builder.add_tracks(tracks)
            .with_filter(TrackHasMetadataSpecification())
            .with_pipeline(pipeline)
            .with_limit(2)
            .build()
        )

        # Filter removes track 3, pipeline removes duplicate of 1, limit to 2
        assert len(result) == 2

    def test_method_chaining(self):
        """Test fluent API with method chaining."""
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = TrackCollectionBuilder().add_tracks(tracks).with_limit(1).build()

        assert len(result) == 1

    def test_add_none_track_skipped(self):
        """Test that None track is skipped."""
        builder = TrackCollectionBuilder()

        result = builder.add_track(None).build()

        assert len(result) == 0
