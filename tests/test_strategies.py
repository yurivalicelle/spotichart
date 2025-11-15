"""
Tests for Strategy Pattern (Playlist Update Strategies)
"""

import pytest
from unittest.mock import Mock, call

from spotichart.core.strategies import (
    AppendStrategy,
    ReplaceStrategy,
    UpdateStrategyFactory,
)


class TestReplaceStrategy:
    """Test ReplaceStrategy."""

    def test_replace_empty_playlist(self):
        """Replace strategy with empty playlist."""
        strategy = ReplaceStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {"items": [], "next": None}
        playlist_reader.next.return_value = None

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1", "uri2", "uri3"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify
        assert count == 3
        playlist_reader.playlist_tracks.assert_called_once_with("playlist123")
        track_writer.playlist_add_items.assert_called_once()

    def test_replace_existing_tracks(self):
        """Replace strategy removes existing tracks first."""
        strategy = ReplaceStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {"track": {"uri": "existing1"}},
                {"track": {"uri": "existing2"}},
            ],
            "next": None,
        }
        playlist_reader.next.return_value = None

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}
        track_writer.playlist_remove_all_occurrences_of_items.return_value = {}

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1", "uri2"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify - should remove existing tracks
        track_writer.playlist_remove_all_occurrences_of_items.assert_called_once_with(
            "playlist123", ["existing1", "existing2"]
        )

        # Should add new tracks
        assert count == 2
        track_writer.playlist_add_items.assert_called_once()

    def test_replace_with_pagination(self):
        """Replace strategy handles paginated results."""
        strategy = ReplaceStrategy()

        # Mock dependencies with pagination
        playlist_reader = Mock()
        first_page = {
            "items": [{"track": {"uri": "existing1"}}],
            "next": "next_url",
        }
        second_page = {"items": [{"track": {"uri": "existing2"}}], "next": None}

        playlist_reader.playlist_tracks.return_value = first_page
        playlist_reader.next.side_effect = [second_page]

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}
        track_writer.playlist_remove_all_occurrences_of_items.return_value = {}

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify pagination was handled (called once to get second page)
        assert playlist_reader.next.call_count == 1

        # Should remove all existing tracks from both pages
        track_writer.playlist_remove_all_occurrences_of_items.assert_called_once_with(
            "playlist123", ["existing1", "existing2"]
        )

    def test_replace_batching(self):
        """Replace strategy batches tracks in groups of 100."""
        strategy = ReplaceStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {"items": [], "next": None}

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}

        # Create 250 tracks (should be split into 3 batches)
        track_uris = [f"uri{i}" for i in range(250)]

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=track_uris,
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify batching (100 + 100 + 50)
        assert count == 250
        assert track_writer.playlist_add_items.call_count == 3


class TestAppendStrategy:
    """Test AppendStrategy."""

    def test_append_to_empty_playlist(self):
        """Append strategy with empty playlist."""
        strategy = AppendStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {"items": [], "next": None}
        playlist_reader.next.return_value = None

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1", "uri2", "uri3"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify
        assert count == 3
        track_writer.playlist_add_items.assert_called_once()

    def test_append_filters_duplicates(self):
        """Append strategy filters out existing tracks."""
        strategy = AppendStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {"track": {"uri": "uri1"}},
                {"track": {"uri": "uri2"}},
            ],
            "next": None,
        }
        playlist_reader.next.return_value = None

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}

        # Execute - uri1 and uri2 already exist
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1", "uri2", "uri3", "uri4"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify - should only add uri3 and uri4
        assert count == 2
        track_writer.playlist_add_items.assert_called_once()

        # Check that only new tracks were added
        call_args = track_writer.playlist_add_items.call_args
        added_uris = call_args[0][1]
        assert set(added_uris) == {"uri3", "uri4"}

    def test_append_no_new_tracks(self):
        """Append strategy when all tracks already exist."""
        strategy = AppendStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {
            "items": [
                {"track": {"uri": "uri1"}},
                {"track": {"uri": "uri2"}},
            ],
            "next": None,
        }

        playlist_writer = Mock()
        track_writer = Mock()

        # Execute - all tracks already exist
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=["uri1", "uri2"],
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify - should not add any tracks
        assert count == 0
        track_writer.playlist_add_items.assert_not_called()

    def test_append_batching(self):
        """Append strategy batches tracks in groups of 100."""
        strategy = AppendStrategy()

        # Mock dependencies
        playlist_reader = Mock()
        playlist_reader.playlist_tracks.return_value = {"items": [], "next": None}

        playlist_writer = Mock()
        track_writer = Mock()
        track_writer.playlist_add_items.return_value = {}

        # Create 250 tracks
        track_uris = [f"uri{i}" for i in range(250)]

        # Execute
        count = strategy.update(
            playlist_id="playlist123",
            track_uris=track_uris,
            playlist_reader=playlist_reader,
            playlist_writer=playlist_writer,
            track_writer=track_writer,
        )

        # Verify batching (100 + 100 + 50)
        assert count == 250
        assert track_writer.playlist_add_items.call_count == 3


class TestUpdateStrategyFactory:
    """Test UpdateStrategyFactory."""

    def test_create_replace_strategy(self):
        """Factory should create ReplaceStrategy."""
        strategy = UpdateStrategyFactory.create("replace")
        assert isinstance(strategy, ReplaceStrategy)

    def test_create_append_strategy(self):
        """Factory should create AppendStrategy."""
        strategy = UpdateStrategyFactory.create("append")
        assert isinstance(strategy, AppendStrategy)

    def test_create_case_insensitive(self):
        """Factory should be case insensitive."""
        strategy1 = UpdateStrategyFactory.create("REPLACE")
        strategy2 = UpdateStrategyFactory.create("Append")
        assert isinstance(strategy1, ReplaceStrategy)
        assert isinstance(strategy2, AppendStrategy)

    def test_create_invalid_mode(self):
        """Factory should raise ValueError for invalid mode."""
        with pytest.raises(ValueError, match="Unknown update mode"):
            UpdateStrategyFactory.create("invalid")
