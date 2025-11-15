from abc import ABC, abstractmethod

class IConfiguration(ABC):
    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def validate(self):
        pass

class ISpotifyAuth(ABC):
    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def get_user_id(self) -> str:
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
    def search(self, track_id: str):
        pass

    @abstractmethod
    def build_uri(self, track_id: str) -> str:
        pass
