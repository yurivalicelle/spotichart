from .interfaces import IPlaylistOperations, ITrackOperations


class SpotifyService:
    def __init__(self, playlists: IPlaylistOperations, tracks: ITrackOperations):
        self.playlists = playlists
        self.tracks = tracks

    def create_playlist_with_tracks(
        self, name: str, track_ids: list, description: str = "", public: bool = False
    ):
        playlist = self.playlists.create(name, description, public)
        if not track_ids:
            return playlist["external_urls"]["spotify"], 0, []

        track_uris = [self.tracks.build_uri(tid) for tid in track_ids]
        added_count = self.tracks.add_to_playlist(playlist["id"], track_uris)

        failed_tracks = []  # Simplified for now
        return playlist["external_urls"]["spotify"], added_count, failed_tracks

    def create_or_update_playlist(
        self,
        name: str,
        track_ids: list,
        description: str = "",
        public: bool = False,
        update_mode: str = "replace",
    ):
        existing_playlist = self.playlists.find_by_name(name)

        if existing_playlist:
            playlist_id = existing_playlist["id"]
            if update_mode == "replace":
                self.playlists.clear(playlist_id)

            track_uris = [self.tracks.build_uri(tid) for tid in track_ids]
            added_count = self.tracks.add_to_playlist(playlist_id, track_uris)

            if description:
                self.playlists.update_details(playlist_id, description)

            return existing_playlist["external_urls"]["spotify"], added_count, [], True
        else:
            url, count, failed = self.create_playlist_with_tracks(
                name, track_ids, description, public
            )
            return url, count, failed, False

    def list_playlists(self, limit: int = 50):
        return self.playlists.get_all(limit=limit)
