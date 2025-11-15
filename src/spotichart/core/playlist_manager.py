import json
from datetime import datetime, timedelta
from pathlib import Path
from .interfaces import ISpotifyAuth
from ..utils.exceptions import PlaylistCreationError

class PlaylistManager:
    def __init__(self, auth: ISpotifyAuth, cache_ttl_hours: int = 24):
        self.auth = auth
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.cache_file = Path.home() / '.spotichart' / 'cache' / 'playlists.json'
        self._playlist_cache = self._load_cache()

    def _load_cache(self):
        if not self.cache_file.exists():
            return {}
        with open(self.cache_file, 'r') as f:
            try:
                cache_data = json.load(f)
                # Filter out expired entries
                now = datetime.now()
                valid_cache = {}
                for key, value in cache_data.items():
                    cached_at = datetime.fromisoformat(value.get('cached_at', ''))
                    if now - cached_at < self.cache_ttl:
                        valid_cache[key] = value['playlist']
                return valid_cache
            except json.JSONDecodeError:
                return {}

    def _save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now().isoformat()
        cache_data = {key: {'playlist': value, 'cached_at': now} for key, value in self._playlist_cache.items()}
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)

    def create(self, name: str, description: str, public: bool = False):
        try:
            client = self.auth.get_client()
            user_id = self.auth.get_user_id()
            playlist = client.user_playlist_create(user=user_id, name=name, public=public, description=description)
            self._playlist_cache[name.lower()] = playlist
            self._save_cache()
            return playlist
        except Exception as e:
            raise PlaylistCreationError(f"Playlist creation failed: {e}") from e

    def find_by_name(self, name: str):
        if name.lower() in self._playlist_cache:
            return self._playlist_cache[name.lower()]
        
        client = self.auth.get_client()
        offset = 0
        limit = 50
        while True:
            playlists = client.current_user_playlists(limit=limit, offset=offset)
            for item in playlists['items']:
                if item['name'].lower() == name.lower():
                    self._playlist_cache[name.lower()] = item
                    self._save_cache()
                    return item
            if not playlists['next']:
                break
            offset += limit
        return None

    def clear(self, playlist_id: str):
        try:
            client = self.auth.get_client()
            tracks = []
            results = client.playlist_tracks(playlist_id)
            tracks.extend(results['items'])
            while results['next']:
                results = client.next(results)
                tracks.extend(results['items'])
            
            track_uris = [item['track']['uri'] for item in tracks if item['track']]
            if track_uris:
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i+100]
                    client.playlist_remove_all_occurrences_of_items(playlist_id, batch)
            return True
        except Exception:
            return False

    def update_details(self, playlist_id: str, description: str):
        if not description:
            return False
        try:
            client = self.auth.get_client()
            client.playlist_change_details(playlist_id, description=description)
            return True
        except Exception:
            return False

    def get_all(self, limit: int = 50):
        try:
            client = self.auth.get_client()
            return client.current_user_playlists(limit=limit)['items']
        except Exception:
            return []
