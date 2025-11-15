"""Tests for Pipeline Pattern."""

from unittest.mock import Mock

import pytest

from spotichart.core.models import Track
from spotichart.domain.pipelines import (
    EnrichTrackMetadataStep,
    FilterBySpecificationStep,
    LimitTracksStep,
    Pipeline,
    RemoveDuplicatesStep,
    SortTracksStep,
    ValidateTrackStep,
)
from spotichart.domain.specifications import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    TrackHasMetadataSpecification,
    TrackIdValidSpecification,
)


class TestPipeline:
    """Tests for Pipeline class."""

    def test_empty_pipeline(self):
        """Test pipeline with no steps."""
        pipeline = Pipeline()
        tracks = [Track(id="1", name="Song", artist="Artist")]

        result = pipeline.execute(tracks)

        assert result == tracks

    def test_single_step(self):
        """Test pipeline with single step."""
        pipeline = Pipeline()
        pipeline.add_step(ValidateTrackStep())

        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id=None, name="Invalid", artist="Artist"),
        ]

        result = pipeline.execute(tracks)

        assert len(result) == 1
        assert result[0].id == "1"

    def test_multiple_steps(self):
        """Test pipeline with multiple steps."""
        pipeline = Pipeline()
        pipeline.add_step(ValidateTrackStep())
        pipeline.add_step(LimitTracksStep(2))

        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="3", name="Song3", artist="Artist"),
        ]

        result = pipeline.execute(tracks)

        assert len(result) == 2

    def test_method_chaining(self):
        """Test pipeline builder pattern with method chaining."""
        pipeline = Pipeline().add_step(ValidateTrackStep()).add_step(LimitTracksStep(1))

        tracks = [Track(id="1", name="Song", artist="Artist")]

        result = pipeline.execute(tracks)

        assert len(result) == 1

    def test_clear_steps(self):
        """Test clearing pipeline steps."""
        pipeline = Pipeline()
        pipeline.add_step(ValidateTrackStep())
        pipeline.add_step(LimitTracksStep(1))

        pipeline.clear()

        tracks = [Track(id="1", name="Song", artist="Artist")]
        result = pipeline.execute(tracks)

        assert result == tracks


class TestValidateTrackStep:
    """Tests for ValidateTrackStep."""

    def test_validate_all_valid(self):
        """Test validation with all valid tracks."""
        step = ValidateTrackStep()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2

    def test_validate_some_invalid(self):
        """Test validation with some invalid tracks."""
        step = ValidateTrackStep()
        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id=None, name="Invalid", artist="Artist"),
            Track(id="", name="Empty", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].id == "1"

    def test_validate_with_custom_specification(self):
        """Test validation with custom specification."""
        spec = TrackHasMetadataSpecification()
        step = ValidateTrackStep(specification=spec)

        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id="2", name=None, artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].name == "Song"


class TestRemoveDuplicatesStep:
    """Tests for RemoveDuplicatesStep."""

    def test_no_duplicates(self):
        """Test with no duplicate tracks."""
        step = RemoveDuplicatesStep()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2

    def test_with_duplicates(self):
        """Test removing duplicate tracks."""
        step = RemoveDuplicatesStep()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="1", name="Song1 Duplicate", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"
        # First occurrence should be kept
        assert result[0].name == "Song1"

    def test_all_duplicates(self):
        """Test with all duplicate tracks."""
        step = RemoveDuplicatesStep()
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="1", name="Song1 Copy", artist="Artist"),
            Track(id="1", name="Song1 Another", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].id == "1"


class TestFilterBySpecificationStep:
    """Tests for FilterBySpecificationStep."""

    def test_filter_all_pass(self):
        """Test filtering where all tracks pass."""
        spec = AlwaysTrueSpecification()
        step = FilterBySpecificationStep(spec)

        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2

    def test_filter_none_pass(self):
        """Test filtering where no tracks pass."""
        spec = AlwaysFalseSpecification()
        step = FilterBySpecificationStep(spec)

        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 0

    def test_filter_some_pass(self):
        """Test filtering where some tracks pass."""
        spec = TrackHasMetadataSpecification()
        step = FilterBySpecificationStep(spec)

        tracks = [
            Track(id="1", name="Song", artist="Artist"),
            Track(id="2", name=None, artist="Artist"),
            Track(id="3", name="Song2", artist=None),
        ]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].id == "1"


class TestLimitTracksStep:
    """Tests for LimitTracksStep."""

    def test_limit_below_count(self):
        """Test limiting when limit is below track count."""
        step = LimitTracksStep(2)
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="3", name="Song3", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_limit_above_count(self):
        """Test limiting when limit is above track count."""
        step = LimitTracksStep(10)
        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
        ]

        result = step.process(tracks)

        assert len(result) == 2

    def test_limit_zero(self):
        """Test limiting to zero tracks."""
        step = LimitTracksStep(0)
        tracks = [Track(id="1", name="Song1", artist="Artist")]

        result = step.process(tracks)

        assert len(result) == 0


class TestEnrichTrackMetadataStep:
    """Tests for EnrichTrackMetadataStep."""

    def test_enrich_tracks_without_metadata(self):
        """Test enriching tracks that lack metadata."""
        mock_reader = Mock()
        mock_reader.track.return_value = {
            "name": "Enriched Song",
            "artists": [{"name": "Enriched Artist"}],
            "album": {"name": "Enriched Album"},
        }

        step = EnrichTrackMetadataStep(mock_reader)
        tracks = [Track(id="1", name=None, artist=None)]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].name == "Enriched Song"
        assert result[0].artist == "Enriched Artist"
        assert result[0].album == "Enriched Album"
        mock_reader.track.assert_called_once_with("1")

    def test_skip_tracks_with_metadata(self):
        """Test that tracks with metadata are not enriched."""
        mock_reader = Mock()

        step = EnrichTrackMetadataStep(mock_reader)
        tracks = [Track(id="1", name="Existing", artist="Existing Artist")]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].name == "Existing"
        assert result[0].artist == "Existing Artist"
        mock_reader.track.assert_not_called()

    def test_enrich_missing_metadata(self):
        """Test enriching when API returns None."""
        mock_reader = Mock()
        mock_reader.track.return_value = None

        step = EnrichTrackMetadataStep(mock_reader)
        tracks = [Track(id="1", name=None, artist=None)]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].name is None
        assert result[0].artist is None

    def test_enrich_partial_metadata(self):
        """Test enriching tracks with partial metadata."""
        mock_reader = Mock()
        mock_reader.track.return_value = {
            "name": "Song",
            "artists": [],  # Empty artists
        }

        step = EnrichTrackMetadataStep(mock_reader)
        tracks = [Track(id="1", name=None, artist=None)]

        result = step.process(tracks)

        assert len(result) == 1
        assert result[0].name == "Song"
        assert result[0].artist is None


class TestSortTracksStep:
    """Tests for SortTracksStep."""

    def test_sort_with_key_function(self):
        """Test sorting tracks with a key function."""
        step = SortTracksStep(key_func=lambda t: t.name)
        tracks = [
            Track(id="1", name="C", artist="Artist"),
            Track(id="2", name="A", artist="Artist"),
            Track(id="3", name="B", artist="Artist"),
        ]

        result = step.process(tracks)

        assert result[0].name == "A"
        assert result[1].name == "B"
        assert result[2].name == "C"

    def test_sort_reverse(self):
        """Test sorting tracks in reverse order."""
        step = SortTracksStep(key_func=lambda t: t.name, reverse=True)
        tracks = [
            Track(id="1", name="A", artist="Artist"),
            Track(id="2", name="B", artist="Artist"),
            Track(id="3", name="C", artist="Artist"),
        ]

        result = step.process(tracks)

        assert result[0].name == "C"
        assert result[1].name == "B"
        assert result[2].name == "A"

    def test_sort_without_key_preserves_order(self):
        """Test that sorting without key function preserves order."""
        step = SortTracksStep()
        tracks = [
            Track(id="1", name="C", artist="Artist"),
            Track(id="2", name="A", artist="Artist"),
        ]

        result = step.process(tracks)

        assert result[0].name == "C"
        assert result[1].name == "A"


class TestPipelineIntegration:
    """Integration tests for complete pipelines."""

    def test_full_processing_pipeline(self):
        """Test a complete processing pipeline."""
        pipeline = (
            Pipeline()
            .add_step(ValidateTrackStep())
            .add_step(RemoveDuplicatesStep())
            .add_step(LimitTracksStep(2))
        )

        tracks = [
            Track(id="1", name="Song1", artist="Artist"),
            Track(id="2", name="Song2", artist="Artist"),
            Track(id="1", name="Song1 Dup", artist="Artist"),  # Duplicate
            Track(id=None, name="Invalid", artist="Artist"),  # Invalid
            Track(id="3", name="Song3", artist="Artist"),
        ]

        result = pipeline.execute(tracks)

        # Should validate (remove invalid), dedupe, and limit to 2
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_filter_and_sort_pipeline(self):
        """Test pipeline with filtering and sorting."""
        pipeline = (
            Pipeline()
            .add_step(FilterBySpecificationStep(TrackHasMetadataSpecification()))
            .add_step(SortTracksStep(key_func=lambda t: t.name))
        )

        tracks = [
            Track(id="1", name="C", artist="Artist"),
            Track(id="2", name=None, artist="Artist"),  # Will be filtered
            Track(id="3", name="A", artist="Artist"),
            Track(id="4", name="B", artist="Artist"),
        ]

        result = pipeline.execute(tracks)

        assert len(result) == 3
        assert result[0].name == "A"
        assert result[1].name == "B"
        assert result[2].name == "C"
