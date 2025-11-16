"""
Tests to improve coverage of interface files.
"""

import pytest

from spotichart.core.interfaces import (
    IPlaylistReader,
    IPlaylistWriter,
    ISpotifyAuth,
    ISpotifyUserAuth,
    ITrackReader,
    ITrackWriter,
)
from spotichart.utils.interfaces import IConfiguration


class ConcreteConfiguration(IConfiguration):
    """Concrete implementation for testing."""

    def get(self, key: str, default=None):
        """Get config value."""
        return default if key == "missing" else "test_value"

    def validate(self) -> bool:
        """Validate configuration."""
        return True


class TestUtilsInterfaces:
    """Test utils interfaces."""

    def test_configuration_interface_get(self):
        """Test IConfiguration.get method."""
        config = ConcreteConfiguration()

        assert config.get("test_key") == "test_value"
        assert config.get("missing", "default_value") == "default_value"

    def test_configuration_interface_validate(self):
        """Test IConfiguration.validate method."""
        config = ConcreteConfiguration()

        assert config.validate() is True


class ConcreteSpotifyUserAuth(ISpotifyUserAuth):
    """Concrete implementation for testing."""

    @property
    def user_id(self) -> str:
        """Get user ID."""
        return "test_user"


class ConcretePlaylistReader(IPlaylistReader):
    """Concrete implementation for testing."""

    def current_user_playlists(self, limit: int = 50, offset: int = 0):
        """Get playlists."""
        return {"items": []}

    def playlist_tracks(self, playlist_id: str):
        """Get tracks."""
        return {"items": []}

    def next(self, result):
        """Get next page."""
        return None


class ConcretePlaylistWriter(IPlaylistWriter):
    """Concrete implementation for testing."""

    def user_playlist_create(self, user: str, name: str, public: bool = False, description: str = ""):
        """Create playlist."""
        return {"id": "new_playlist"}

    def playlist_change_details(
        self,
        playlist_id: str,
        name=None,
        public=None,
        collaborative=None,
        description=None,
    ):
        """Change details."""
        pass


class ConcreteTrackReader(ITrackReader):
    """Concrete implementation for testing."""

    def track(self, track_id: str):
        """Get track."""
        return {"id": track_id, "name": "Test Track"}


class ConcreteTrackWriter(ITrackWriter):
    """Concrete implementation for testing."""

    def playlist_add_items(self, playlist_id: str, items, position=None):
        """Add items."""
        return {"snapshot_id": "test"}

    def playlist_remove_all_occurrences_of_items(self, playlist_id: str, items):
        """Remove items."""
        return {"snapshot_id": "test"}


class ConcreteSpotifyAuth(ISpotifyAuth):
    """Concrete implementation for testing."""

    def get_client(self):
        """Get client."""
        return "client"

    def get_user_id(self) -> str:
        """Get user ID."""
        return "test_user"


class TestCoreInterfaces:
    """Test core interfaces."""

    def test_spotify_user_auth_interface(self):
        """Test ISpotifyUserAuth interface."""
        auth = ConcreteSpotifyUserAuth()
        assert auth.user_id == "test_user"

    def test_playlist_reader_interface(self):
        """Test IPlaylistReader interface."""
        reader = ConcretePlaylistReader()

        playlists = reader.current_user_playlists(limit=10)
        assert "items" in playlists

        tracks = reader.playlist_tracks("test_id")
        assert "items" in tracks

        next_page = reader.next({"items": []})
        assert next_page is None

    def test_playlist_writer_interface(self):
        """Test IPlaylistWriter interface."""
        writer = ConcretePlaylistWriter()

        result = writer.user_playlist_create("user", "Test Playlist", public=True, description="Test")
        assert result["id"] == "new_playlist"

        # Should not raise
        writer.playlist_change_details("playlist_id", name="New Name")

    def test_track_reader_interface(self):
        """Test ITrackReader interface."""
        reader = ConcreteTrackReader()

        track = reader.track("track123")
        assert track["id"] == "track123"

    def test_track_writer_interface(self):
        """Test ITrackWriter interface."""
        writer = ConcreteTrackWriter()

        result = writer.playlist_add_items("playlist_id", ["track1", "track2"])
        assert "snapshot_id" in result

        result = writer.playlist_remove_all_occurrences_of_items("playlist_id", ["track1"])
        assert "snapshot_id" in result

    def test_spotify_auth_interface(self):
        """Test ISpotifyAuth (legacy) interface."""
        auth = ConcreteSpotifyAuth()

        assert auth.get_client() == "client"
        assert auth.get_user_id() == "test_user"
