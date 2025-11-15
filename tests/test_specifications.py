"""Tests for Specification Pattern."""

import pytest

from spotichart.core.models import Track
from spotichart.domain.specifications import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    AndSpecification,
    NotSpecification,
    OrSpecification,
    TrackHasMetadataSpecification,
    TrackIdValidSpecification,
)


class TestTrackIdValidSpecification:
    """Tests for TrackIdValidSpecification."""

    def test_valid_track_id(self):
        """Test that track with valid ID satisfies specification."""
        spec = TrackIdValidSpecification()
        track = Track(id="spotify123", name="Test", artist="Artist")

        assert spec.is_satisfied_by(track) is True

    def test_none_track_id(self):
        """Test that track with None ID does not satisfy specification."""
        spec = TrackIdValidSpecification()
        track = Track(id=None, name="Test", artist="Artist")

        assert spec.is_satisfied_by(track) is False

    def test_empty_track_id(self):
        """Test that track with empty ID does not satisfy specification."""
        spec = TrackIdValidSpecification()
        track = Track(id="", name="Test", artist="Artist")

        assert spec.is_satisfied_by(track) is False

    def test_whitespace_track_id(self):
        """Test that track with whitespace ID does not satisfy specification."""
        spec = TrackIdValidSpecification()
        track = Track(id="   ", name="Test", artist="Artist")

        assert spec.is_satisfied_by(track) is False


class TestTrackHasMetadataSpecification:
    """Tests for TrackHasMetadataSpecification."""

    def test_track_with_metadata(self):
        """Test that track with name and artist satisfies specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name="Song", artist="Artist")

        assert spec.is_satisfied_by(track) is True

    def test_track_without_name(self):
        """Test that track without name does not satisfy specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name=None, artist="Artist")

        assert spec.is_satisfied_by(track) is False

    def test_track_without_artist(self):
        """Test that track without artist does not satisfy specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name="Song", artist=None)

        assert spec.is_satisfied_by(track) is False

    def test_track_with_empty_name(self):
        """Test that track with empty name does not satisfy specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name="", artist="Artist")

        assert spec.is_satisfied_by(track) is False

    def test_track_with_empty_artist(self):
        """Test that track with empty artist does not satisfy specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name="Song", artist="")

        assert spec.is_satisfied_by(track) is False

    def test_track_with_whitespace_metadata(self):
        """Test that track with whitespace metadata does not satisfy specification."""
        spec = TrackHasMetadataSpecification()
        track = Track(id="123", name="   ", artist="   ")

        assert spec.is_satisfied_by(track) is False


class TestAndSpecification:
    """Tests for AndSpecification."""

    def test_both_true(self):
        """Test that AND returns True when both specs are satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        and_spec = AndSpecification(spec1, spec2)

        track = Track(id="123", name="Song", artist="Artist")

        assert and_spec.is_satisfied_by(track) is True

    def test_first_false(self):
        """Test that AND returns False when first spec is not satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        and_spec = AndSpecification(spec1, spec2)

        track = Track(id=None, name="Song", artist="Artist")

        assert and_spec.is_satisfied_by(track) is False

    def test_second_false(self):
        """Test that AND returns False when second spec is not satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        and_spec = AndSpecification(spec1, spec2)

        track = Track(id="123", name=None, artist="Artist")

        assert and_spec.is_satisfied_by(track) is False

    def test_both_false(self):
        """Test that AND returns False when both specs are not satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        and_spec = AndSpecification(spec1, spec2)

        track = Track(id=None, name=None, artist=None)

        assert and_spec.is_satisfied_by(track) is False

    def test_and_method(self):
        """Test using and_ method for fluent API."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        and_spec = spec1.and_(spec2)

        track = Track(id="123", name="Song", artist="Artist")

        assert and_spec.is_satisfied_by(track) is True


class TestOrSpecification:
    """Tests for OrSpecification."""

    def test_both_true(self):
        """Test that OR returns True when both specs are satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        or_spec = OrSpecification(spec1, spec2)

        track = Track(id="123", name="Song", artist="Artist")

        assert or_spec.is_satisfied_by(track) is True

    def test_first_true_second_false(self):
        """Test that OR returns True when first spec is satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        or_spec = OrSpecification(spec1, spec2)

        track = Track(id="123", name=None, artist=None)

        assert or_spec.is_satisfied_by(track) is True

    def test_first_false_second_true(self):
        """Test that OR returns True when second spec is satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        or_spec = OrSpecification(spec1, spec2)

        track = Track(id=None, name="Song", artist="Artist")

        assert or_spec.is_satisfied_by(track) is True

    def test_both_false(self):
        """Test that OR returns False when both specs are not satisfied."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        or_spec = OrSpecification(spec1, spec2)

        track = Track(id=None, name=None, artist=None)

        assert or_spec.is_satisfied_by(track) is False

    def test_or_method(self):
        """Test using or_ method for fluent API."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        or_spec = spec1.or_(spec2)

        track = Track(id="123", name=None, artist=None)

        assert or_spec.is_satisfied_by(track) is True


class TestNotSpecification:
    """Tests for NotSpecification."""

    def test_negate_true(self):
        """Test that NOT negates a satisfied specification."""
        spec = TrackIdValidSpecification()
        not_spec = NotSpecification(spec)

        track = Track(id="123", name="Song", artist="Artist")

        assert not_spec.is_satisfied_by(track) is False

    def test_negate_false(self):
        """Test that NOT negates an unsatisfied specification."""
        spec = TrackIdValidSpecification()
        not_spec = NotSpecification(spec)

        track = Track(id=None, name="Song", artist="Artist")

        assert not_spec.is_satisfied_by(track) is True

    def test_not_method(self):
        """Test using not_ method for fluent API."""
        spec = TrackIdValidSpecification()
        not_spec = spec.not_()

        track = Track(id=None, name="Song", artist="Artist")

        assert not_spec.is_satisfied_by(track) is True


class TestAlwaysTrueSpecification:
    """Tests for AlwaysTrueSpecification."""

    def test_always_true(self):
        """Test that specification always returns True."""
        spec = AlwaysTrueSpecification()
        track = Track(id="123", name="Song", artist="Artist")

        assert spec.is_satisfied_by(track) is True

    def test_always_true_with_invalid_track(self):
        """Test that specification returns True even for invalid track."""
        spec = AlwaysTrueSpecification()
        track = Track(id=None, name=None, artist=None)

        assert spec.is_satisfied_by(track) is True


class TestAlwaysFalseSpecification:
    """Tests for AlwaysFalseSpecification."""

    def test_always_false(self):
        """Test that specification always returns False."""
        spec = AlwaysFalseSpecification()
        track = Track(id="123", name="Song", artist="Artist")

        assert spec.is_satisfied_by(track) is False

    def test_always_false_with_invalid_track(self):
        """Test that specification returns False even for invalid track."""
        spec = AlwaysFalseSpecification()
        track = Track(id=None, name=None, artist=None)

        assert spec.is_satisfied_by(track) is False


class TestComplexSpecifications:
    """Tests for complex specification combinations."""

    def test_and_or_combination(self):
        """Test combining AND and OR specifications."""
        id_valid = TrackIdValidSpecification()
        has_metadata = TrackHasMetadataSpecification()

        # (id_valid AND has_metadata) OR always_true
        complex_spec = id_valid.and_(has_metadata).or_(AlwaysTrueSpecification())

        # Should satisfy even without valid ID
        track = Track(id=None, name=None, artist=None)
        assert complex_spec.is_satisfied_by(track) is True

    def test_not_and_combination(self):
        """Test combining NOT and AND specifications."""
        id_valid = TrackIdValidSpecification()
        has_metadata = TrackHasMetadataSpecification()

        # NOT (id_valid AND has_metadata)
        complex_spec = id_valid.and_(has_metadata).not_()

        # Should not satisfy when both are true
        track = Track(id="123", name="Song", artist="Artist")
        assert complex_spec.is_satisfied_by(track) is False

        # Should satisfy when one is false
        track = Track(id=None, name="Song", artist="Artist")
        assert complex_spec.is_satisfied_by(track) is True

    def test_triple_and(self):
        """Test chaining multiple AND specifications."""
        spec1 = TrackIdValidSpecification()
        spec2 = TrackHasMetadataSpecification()
        spec3 = AlwaysTrueSpecification()

        complex_spec = spec1.and_(spec2).and_(spec3)

        track = Track(id="123", name="Song", artist="Artist")
        assert complex_spec.is_satisfied_by(track) is True

        track = Track(id=None, name="Song", artist="Artist")
        assert complex_spec.is_satisfied_by(track) is False
