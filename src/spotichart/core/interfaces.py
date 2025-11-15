from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class ISpotifyAuth(ABC):
    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def get_user_id(self) -> str:
        pass

class ISpotifyClient(ABC):
    """Interface for Spotify API client operations."""

    @property
    @abstractmethod
    def user_id(self) -> str:
        """Get current user ID."""
        pass

    @abstractmethod
    def user_playlist_create(self, user: str, name: str, public: bool = False, description: str = '') -> Dict:
        """Create a new playlist."""
        pass

    @abstractmethod
    def current_user_playlists(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get current user's playlists."""
        pass

    @abstractmethod
    def playlist_tracks(self, playlist_id: str) -> Dict:
        """Get tracks from a playlist."""
        pass

    @abstractmethod
    def next(self, result: Dict) -> Optional[Dict]:
        """Get next page of results."""
        pass

    @abstractmethod
    def playlist_remove_all_occurrences_of_items(self, playlist_id: str, items: List[str]) -> Dict:
        """Remove all occurrences of tracks from playlist."""
        pass

    @abstractmethod
    def playlist_change_details(self, playlist_id: str, name: Optional[str] = None,
                                public: Optional[bool] = None, collaborative: Optional[bool] = None,
                                description: Optional[str] = None) -> None:
        """Change playlist details."""
        pass

    @abstractmethod
    def playlist_add_items(self, playlist_id: str, items: List[str], position: Optional[int] = None) -> Dict:
        """Add tracks to a playlist."""
        pass

    @abstractmethod
    def track(self, track_id: str) -> Optional[Dict]:
        """Get track information by ID."""
        pass

class IPlaylistOperations(ABC):
    @abstractmethod
    def create(self, name: str, description: str, public: bool = False):
        pass

    @abstractmethod
    def find_by_name(self, name: str):
        pass

    @abstractmethod
    def clear(self, playlist_id: str):
        pass

    @abstractmethod
    def update_details(self, playlist_id: str, description: str):
        pass

    @abstractmethod
    def get_all(self, limit: int = 50):
        pass

class ITrackOperations(ABC):
    @abstractmethod
    def add_to_playlist(self, playlist_id: str, track_uris: list):
        pass

    @abstractmethod
    def build_uri(self, track_id: str) -> str:
        pass
