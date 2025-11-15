"""Tests for SpotifyService facade."""

from unittest.mock import Mock

import pytest

from spotichart.core.spotify_service import SpotifyService


class TestSpotifyServiceInit:
    """Test SpotifyService initialization."""

    def test_init_with_managers(self, mock_playlist_operations, mock_track_operations):
        """Initialize with playlist and track managers."""
        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        assert service.playlists == mock_playlist_operations
        assert service.tracks == mock_track_operations


class TestSpotifyServiceCreatePlaylist:
    """Test creating playlists via facade."""

    def test_create_playlist_with_tracks(self, mock_playlist_operations, mock_track_operations):
        """Create playlist with tracks."""
        mock_playlist_operations.create.return_value = {
            "id": "playlist_123",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist_123"},
        }
        mock_track_operations.add_to_playlist.return_value = 5

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        url, count, failed = service.create_playlist_with_tracks(
            name="Test Playlist",
            track_ids=["track1", "track2", "track3", "track4", "track5"],
            description="Test",
        )

        assert url == "https://open.spotify.com/playlist/playlist_123"
        assert count == 5
        assert isinstance(failed, list)

        mock_playlist_operations.create.assert_called_once()
        mock_track_operations.add_to_playlist.assert_called_once()

    def test_create_playlist_empty_tracks(self, mock_playlist_operations, mock_track_operations):
        """Create playlist with no tracks."""
        mock_playlist_operations.create.return_value = {
            "id": "playlist_123",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist_123"},
        }

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        url, count, failed = service.create_playlist_with_tracks(
            name="Empty Playlist", track_ids=[], description="Empty"
        )

        assert url == "https://open.spotify.com/playlist/playlist_123"
        assert count == 0
        mock_track_operations.add_to_playlist.assert_not_called()


class TestSpotifyServiceCreateOrUpdate:
    """Test create or update playlist."""

    def test_create_when_not_exists(self, mock_playlist_operations, mock_track_operations):
        """Create new playlist when it doesn't exist."""
        mock_playlist_operations.find_by_name.return_value = None
        mock_playlist_operations.create.return_value = {
            "id": "new_playlist",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/new_playlist"},
        }
        mock_track_operations.add_to_playlist.return_value = 3

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        url, count, failed, was_updated = service.create_or_update_playlist(
            name="New Playlist",
            track_ids=["track1", "track2", "track3"],
            description="New",
            update_mode="replace",
        )

        assert url == "https://open.spotify.com/playlist/new_playlist"
        assert count == 3
        assert was_updated is False

        mock_playlist_operations.find_by_name.assert_called_once()
        mock_playlist_operations.create.assert_called_once()

    def test_update_when_exists(self, mock_playlist_operations, mock_track_operations):
        """Update existing playlist."""
        mock_playlist_operations.find_by_name.return_value = {
            "id": "existing_playlist",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/existing_playlist"},
        }
        mock_playlist_operations.clear.return_value = True

        # Mock for new Strategy Pattern (playlist_tracks called by ReplaceStrategy)
        mock_playlist_operations.playlist_tracks.return_value = {"items": [], "next": None}
        mock_playlist_operations.next.return_value = None
        mock_playlist_operations.playlist_remove_all_occurrences_of_items.return_value = {}

        mock_track_operations.add_to_playlist.return_value = 5
        mock_track_operations.playlist_add_items.return_value = {}

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        url, count, failed, was_updated = service.create_or_update_playlist(
            name="Existing Playlist",
            track_ids=["track1", "track2", "track3", "track4", "track5"],
            description="Updated",
            update_mode="replace",
        )

        assert url == "https://open.spotify.com/playlist/existing_playlist"
        assert count == 5
        assert was_updated is True

        mock_playlist_operations.find_by_name.assert_called_once()

    def test_update_append_mode(self, mock_playlist_operations, mock_track_operations):
        """Update in append mode doesn't clear."""
        mock_playlist_operations.find_by_name.return_value = {
            "id": "existing_playlist",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/existing_playlist"},
        }

        # Mock for new Strategy Pattern (playlist_tracks called by AppendStrategy)
        mock_playlist_operations.playlist_tracks.return_value = {"items": [], "next": None}
        mock_playlist_operations.next.return_value = None

        mock_track_operations.add_to_playlist.return_value = 3
        mock_track_operations.playlist_add_items.return_value = {}

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        url, count, failed, was_updated = service.create_or_update_playlist(
            name="Existing Playlist", track_ids=["track1", "track2", "track3"], update_mode="append"
        )

        assert was_updated is True
        mock_playlist_operations.clear.assert_not_called()  # Append mode doesn't clear


class TestSpotifyServiceListPlaylists:
    """Test listing playlists."""

    def test_list_playlists(self, mock_playlist_operations, mock_track_operations):
        """List user playlists."""
        mock_playlist_operations.get_all.return_value = [
            {"id": "1", "name": "Playlist 1"},
            {"id": "2", "name": "Playlist 2"},
        ]

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        playlists = service.list_playlists(limit=50)

        assert len(playlists) == 2
        assert playlists[0]["id"] == "1"
        mock_playlist_operations.get_all.assert_called_once_with(limit=50)


class TestSpotifyServiceFacadePattern:
    """Test that SpotifyService properly implements Facade pattern."""

    def test_delegates_to_playlist_manager(self, mock_playlist_operations, mock_track_operations):
        """Delegates playlist operations to playlist manager."""
        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        # All playlist operations should delegate
        service.playlists.create("Test", "Desc")
        service.playlists.find_by_name("Test")
        service.playlists.get_all()

        assert mock_playlist_operations.create.called
        assert mock_playlist_operations.find_by_name.called
        assert mock_playlist_operations.get_all.called

    def test_delegates_to_track_manager(self, mock_playlist_operations, mock_track_operations):
        """Delegates track operations to track manager."""
        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        # Track operations should delegate
        service.tracks.add_to_playlist("playlist_123", ["track1", "track2"])
        service.tracks.build_uri("track_123")

        assert mock_track_operations.add_to_playlist.called
        assert mock_track_operations.build_uri.called

    def test_provides_simplified_interface(self, mock_playlist_operations, mock_track_operations):
        """Provides simplified high-level interface."""
        mock_playlist_operations.find_by_name.return_value = None
        mock_playlist_operations.create.return_value = {
            "id": "test",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/test"},
        }
        mock_track_operations.add_to_playlist.return_value = 5

        service = SpotifyService(mock_playlist_operations, mock_track_operations)

        # Single method call handles complex workflow
        url, count, failed, updated = service.create_or_update_playlist(
            name="Test", track_ids=["1", "2", "3", "4", "5"]
        )

        # Multiple underlying calls were made
        assert mock_playlist_operations.find_by_name.called
        assert mock_playlist_operations.create.called
        assert mock_track_operations.add_to_playlist.called
