"""
Spotify Service Module

Application service orchestrating playlist and track operations.
Uses Strategy Pattern for flexible playlist update modes.
"""

import logging
from typing import List, Tuple

from .interfaces import (
    IPlaylistOperations,
    IPlaylistReader,
    IPlaylistWriter,
    ITrackOperations,
    ITrackWriter,
)
from .strategies import UpdateStrategyFactory

logger = logging.getLogger(__name__)


class SpotifyService:
    """
    Application service for Spotify operations.

    Orchestrates playlist and track operations using SOLID principles.
    """

    def __init__(
        self,
        playlists: IPlaylistOperations,
        tracks: ITrackOperations,
        playlist_reader: IPlaylistReader = None,
        playlist_writer: IPlaylistWriter = None,
        track_writer: ITrackWriter = None,
    ):
        """
        Initialize service with dependencies.

        Args:
            playlists: Playlist operations interface (legacy)
            tracks: Track operations interface (legacy)
            playlist_reader: Segregated playlist reader (for new Strategy Pattern)
            playlist_writer: Segregated playlist writer (for new Strategy Pattern)
            track_writer: Segregated track writer (for new Strategy Pattern)
        """
        self.playlists = playlists
        self.tracks = tracks

        # Segregated interfaces for Strategy Pattern
        # Fall back to playlists/tracks if not provided (backward compatibility)
        self._playlist_reader = playlist_reader or playlists
        self._playlist_writer = playlist_writer or playlists
        self._track_writer = track_writer or tracks

    def create_playlist_with_tracks(
        self, name: str, track_ids: list, description: str = "", public: bool = False
    ) -> Tuple[str, int, List]:
        """
        Create a new playlist with tracks.

        Args:
            name: Playlist name
            track_ids: List of Spotify track IDs
            description: Playlist description
            public: Whether playlist is public

        Returns:
            Tuple of (playlist_url, added_count, failed_tracks)
        """
        logger.info(f"Creating new playlist: {name}")

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
    ) -> Tuple[str, int, List, bool]:
        """
        Create or update a playlist using Strategy Pattern.

        Args:
            name: Playlist name
            track_ids: List of Spotify track IDs
            description: Playlist description
            public: Whether playlist is public
            update_mode: Update mode ('replace' or 'append')

        Returns:
            Tuple of (playlist_url, added_count, failed_tracks, was_updated)
        """
        logger.info(f"Create or update playlist: {name} (mode: {update_mode})")

        existing_playlist = self.playlists.find_by_name(name)

        if existing_playlist:
            playlist_id = existing_playlist["id"]
            logger.info(f"Found existing playlist: {playlist_id}")

            # Use Strategy Pattern for update
            try:
                strategy = UpdateStrategyFactory.create(update_mode)
                track_uris = [self.tracks.build_uri(tid) for tid in track_ids]

                added_count = strategy.update(
                    playlist_id=playlist_id,
                    track_uris=track_uris,
                    playlist_reader=self._playlist_reader,
                    playlist_writer=self._playlist_writer,
                    track_writer=self._track_writer,
                )

                if description:
                    self.playlists.update_details(playlist_id, description)

                return existing_playlist["external_urls"]["spotify"], added_count, [], True

            except ValueError as e:
                # Invalid update mode - fall back to legacy behavior
                logger.warning(f"Invalid update mode, using legacy: {e}")
                if update_mode == "replace":
                    self.playlists.clear(playlist_id)

                track_uris = [self.tracks.build_uri(tid) for tid in track_ids]
                added_count = self.tracks.add_to_playlist(playlist_id, track_uris)

                if description:
                    self.playlists.update_details(playlist_id, description)

                return existing_playlist["external_urls"]["spotify"], added_count, [], True

        else:
            logger.info(f"Playlist not found, creating new one")
            url, count, failed = self.create_playlist_with_tracks(
                name, track_ids, description, public
            )
            return url, count, failed, False

    def list_playlists(self, limit: int = 50):
        """Get user's playlists."""
        return self.playlists.get_all(limit=limit)
