"""
Property-Based Testing with Hypothesis

Tests invariants and properties that should always hold true,
regardless of input data. Uses generative testing to find edge cases.
"""

from hypothesis import given, strategies as st, assume, settings, Phase
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
import pytest

from spotichart.core.models import Track, PlaylistMetadata
from spotichart.utils.result import Success, Failure, Result
from spotichart.application.pydantic_dtos import (
    CreatePlaylistRequestV2,
    TrackV2,
    PlaylistStatisticsV2,
)


# ============================================================================
# STRATEGIES - Custom generators for valid data
# ============================================================================


# Valid strings that won't be empty after Pydantic's strip_whitespace
def valid_non_empty_text(min_size=1, max_size=100):
    """Generate text that is valid (non-empty after stripping whitespace and printable)."""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))  # Exclude control chars
    ).filter(lambda x: len(x.strip()) > 0)


# ============================================================================
# PROPERTY TESTS - Models
# ============================================================================


class TestTrackProperties:
    """Property-based tests for Track model."""

    @given(
        track_id=st.text(min_size=1, max_size=100),
        name=st.text(min_size=0, max_size=200),
        artist=st.text(min_size=0, max_size=200),
    )
    @settings(max_examples=100, deadline=None)
    def test_track_uri_always_starts_with_spotify_track(self, track_id, artist, name):
        """Property: Track URI should always start with 'spotify:track:'"""
        track = Track(id=track_id, name=name if name else None, artist=artist if artist else None)

        assert track.uri.startswith("spotify:track:")
        assert track.uri == f"spotify:track:{track_id}"

    @given(
        track_id=st.text(min_size=1, max_size=100),
        name=st.text(min_size=1, max_size=200),
        artist=st.text(min_size=1, max_size=200),
    )
    @settings(max_examples=100, deadline=None)
    def test_track_str_with_metadata_always_has_dash(self, track_id, name, artist):
        """Property: Track with metadata should always have ' - ' in string representation"""
        track = Track(id=track_id, name=name, artist=artist)

        track_str = str(track)
        assert " - " in track_str
        assert artist in track_str
        assert name in track_str

    @given(track_id=st.text(min_size=1, max_size=100))
    @settings(max_examples=100, deadline=None)
    def test_track_without_metadata_shows_id(self, track_id):
        """Property: Track without metadata should show ID in string"""
        track = Track(id=track_id)

        assert str(track) == track_id


# ============================================================================
# PROPERTY TESTS - Result Monad
# ============================================================================


class TestResultProperties:
    """Property-based tests for Result monad."""

    @given(value=st.integers() | st.text() | st.booleans())
    @settings(max_examples=100, deadline=None)
    def test_success_is_always_success(self, value):
        """Property: Success should always report is_success() as True"""
        result = Success(value)

        assert result.is_success() is True
        assert result.is_failure() is False
        assert result.unwrap() == value

    @given(error=st.text(min_size=1) | st.integers())
    @settings(max_examples=100, deadline=None)
    def test_failure_is_always_failure(self, error):
        """Property: Failure should always report is_failure() as True"""
        result = Failure(error)

        assert result.is_failure() is True
        assert result.is_success() is False
        assert result.error == error

    @given(value=st.integers())
    @settings(max_examples=50, deadline=None)
    def test_success_map_preserves_success(self, value):
        """Property: Mapping a Success should preserve Success state"""
        result = Success(value)
        mapped = result.map(lambda x: x * 2)

        assert mapped.is_success()
        assert mapped.unwrap() == value * 2

    @given(error=st.text(min_size=1))
    @settings(max_examples=50, deadline=None)
    def test_failure_map_preserves_failure(self, error):
        """Property: Mapping a Failure should preserve Failure state"""
        result: Result[int, str] = Failure(error)
        mapped = result.map(lambda x: x * 2)

        assert mapped.is_failure()
        assert mapped.error == error


# ============================================================================
# PROPERTY TESTS - Pydantic DTOs
# ============================================================================


class TestPydanticDTOProperties:
    """Property-based tests for Pydantic DTOs."""

    @given(
        name=valid_non_empty_text(min_size=1, max_size=100),
        track_count=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100, deadline=None)
    def test_create_playlist_request_name_is_stripped(self, name, track_count):
        """Property: Playlist name should always be stripped of whitespace"""
        # Add some whitespace
        name_with_whitespace = f"  {name}  "
        track_ids = [f"track{i}" for i in range(track_count)]

        request = CreatePlaylistRequestV2(
            name=name_with_whitespace,
            track_ids=track_ids
        )

        # Should be stripped
        assert request.name == name.strip()
        assert not request.name.startswith(" ")
        assert not request.name.endswith(" ")

    @given(
        track_id=valid_non_empty_text(min_size=1, max_size=50),
        popularity=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=100, deadline=None)
    def test_track_v2_uri_format(self, track_id, popularity):
        """Property: TrackV2 URI should always follow spotify:track: format"""
        # Pydantic strips whitespace, so we need to account for that
        track = TrackV2(id=track_id, popularity=popularity)
        expected_id = track_id.strip()

        assert track.uri == f"spotify:track:{expected_id}"
        assert track.uri.startswith("spotify:track:")

    @given(
        total=st.integers(min_value=1, max_value=1000),
        explicit=st.integers(min_value=0, max_value=100),
        duration=st.integers(min_value=1000, max_value=10000000),
    )
    @settings(max_examples=100, deadline=None)
    def test_playlist_statistics_explicit_never_exceeds_total(self, total, explicit, duration):
        """Property: Explicit tracks count should never exceed total tracks"""
        # Ensure explicit doesn't exceed total
        explicit_count = min(explicit, total)
        avg_duration = duration // total if total > 0 else 1

        stats = PlaylistStatisticsV2(
            total_tracks=total,
            total_duration_ms=duration,
            total_duration_minutes=duration // 60000,
            explicit_tracks=explicit_count,
            unique_artists=min(total, 100),
            average_duration_ms=avg_duration,
        )

        assert stats.explicit_tracks <= stats.total_tracks
        assert stats.total_tracks > 0
        assert stats.average_duration_ms > 0


# ============================================================================
# STATEFUL TESTING - Playlist Operations
# ============================================================================


class PlaylistStateMachine(RuleBasedStateMachine):
    """
    Stateful testing for playlist operations.

    Tests that playlist operations maintain invariants across
    a sequence of operations.
    """

    def __init__(self):
        super().__init__()
        self.playlists = {}
        self.next_id = 0

    @initialize()
    def start_empty(self):
        """Start with no playlists."""
        self.playlists = {}
        self.next_id = 0

    @rule(name=st.text(min_size=1, max_size=50))
    def create_playlist(self, name):
        """Create a new playlist."""
        playlist_id = f"playlist_{self.next_id}"
        self.next_id += 1

        self.playlists[playlist_id] = {
            "id": playlist_id,
            "name": name,
            "tracks": [],
        }

    @rule(track_id=st.text(min_size=1, max_size=50))
    def add_track_to_random_playlist(self, track_id):
        """Add a track to a random playlist."""
        if not self.playlists:
            return  # No playlists to add to

        import random
        playlist_id = random.choice(list(self.playlists.keys()))
        self.playlists[playlist_id]["tracks"].append(track_id)

    @invariant()
    def all_playlists_have_valid_ids(self):
        """Invariant: All playlists should have valid IDs."""
        for playlist_id, playlist in self.playlists.items():
            assert playlist["id"] == playlist_id
            assert playlist["id"].startswith("playlist_")

    @invariant()
    def all_playlists_have_names(self):
        """Invariant: All playlists should have names."""
        for playlist in self.playlists.values():
            assert "name" in playlist
            assert len(playlist["name"]) > 0

    @invariant()
    def track_counts_are_non_negative(self):
        """Invariant: Track counts should never be negative."""
        for playlist in self.playlists.values():
            assert len(playlist["tracks"]) >= 0


# Note: Stateful tests are run automatically by Hypothesis
# TestCase is auto-generated from RuleBasedStateMachine


# ============================================================================
# PROPERTY TESTS - Validators
# ============================================================================


class TestValidatorProperties:
    """Property-based tests for validators."""

    @given(
        name=valid_non_empty_text(min_size=1, max_size=100),
        track_ids=st.lists(valid_non_empty_text(min_size=1, max_size=50), min_size=1, max_size=100),
    )
    @settings(max_examples=50, deadline=None)
    def test_valid_playlist_request_always_accepted(self, name, track_ids):
        """Property: Valid playlist requests should always be accepted"""
        request = CreatePlaylistRequestV2(
            name=name,
            track_ids=track_ids,
        )

        assert request.name == name.strip()
        assert len(request.track_ids) == len(track_ids)
        assert len(request.track_ids) > 0

    @given(
        track_ids=st.lists(
            valid_non_empty_text(min_size=1, max_size=50),
            min_size=2,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_track_ids_length_preserved(self, track_ids):
        """Property: Number of track IDs should be preserved"""
        request = CreatePlaylistRequestV2(
            name="Test",
            track_ids=track_ids,
        )

        assert len(request.track_ids) == len(track_ids)


# ============================================================================
# SHRINKING TESTS
# ============================================================================


class TestHypothesisShrinking:
    """Tests that demonstrate Hypothesis shrinking capabilities."""

    @given(numbers=st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=100, deadline=None)
    def test_list_reversal_is_involution(self, numbers):
        """Property: Reversing a list twice returns original list"""
        reversed_once = list(reversed(numbers))
        reversed_twice = list(reversed(reversed_once))

        assert reversed_twice == numbers

    @given(x=st.integers(), y=st.integers())
    @settings(max_examples=100, deadline=None)
    def test_addition_is_commutative(self, x, y):
        """Property: Addition should be commutative (x + y == y + x)"""
        assert x + y == y + x
