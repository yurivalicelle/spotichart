"""
Strategy Pattern Implementations

Different strategies for updating playlists.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from .interfaces import IPlaylistReader, IPlaylistWriter, ITrackWriter

logger = logging.getLogger(__name__)


class IPlaylistUpdateStrategy(ABC):
    """Interface for playlist update strategies (Strategy Pattern)."""

    @abstractmethod
    def update(
        self,
        playlist_id: str,
        track_uris: List[str],
        playlist_reader: IPlaylistReader,
        playlist_writer: IPlaylistWriter,
        track_writer: ITrackWriter,
    ) -> int:
        """
        Update playlist with tracks using specific strategy.

        Args:
            playlist_id: ID of the playlist to update
            track_uris: List of track URIs to add
            playlist_reader: Reader for playlist operations
            playlist_writer: Writer for playlist operations
            track_writer: Writer for track operations

        Returns:
            Number of tracks successfully added
        """
        pass


class ReplaceStrategy(IPlaylistUpdateStrategy):
    """Strategy that replaces all tracks in playlist."""

    def update(
        self,
        playlist_id: str,
        track_uris: List[str],
        playlist_reader: IPlaylistReader,
        playlist_writer: IPlaylistWriter,
        track_writer: ITrackWriter,
    ) -> int:
        """Replace all tracks in the playlist."""
        logger.info(f"Replacing all tracks in playlist {playlist_id}")

        # Get all current tracks
        current_tracks = []
        result = playlist_reader.playlist_tracks(playlist_id)

        while result:
            items = result.get("items", [])
            current_tracks.extend([item["track"]["uri"] for item in items if item.get("track")])
            result = playlist_reader.next(result) if result.get("next") else None

        # Remove all current tracks
        if current_tracks:
            logger.debug(f"Removing {len(current_tracks)} existing tracks")
            batch_size = 100
            for i in range(0, len(current_tracks), batch_size):
                batch = current_tracks[i : i + batch_size]
                track_writer.playlist_remove_all_occurrences_of_items(playlist_id, batch)

        # Add new tracks
        return self._add_tracks_in_batches(playlist_id, track_uris, track_writer)

    def _add_tracks_in_batches(
        self, playlist_id: str, track_uris: List[str], track_writer: ITrackWriter
    ) -> int:
        """Add tracks in batches of 100 (Spotify API limit)."""
        added_count = 0
        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i : i + batch_size]
            try:
                track_writer.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                logger.debug(f"Added batch of {len(batch)} tracks")
            except Exception as e:
                logger.error(f"Failed to add batch: {e}")

        return added_count


class AppendStrategy(IPlaylistUpdateStrategy):
    """Strategy that appends tracks to existing playlist."""

    def update(
        self,
        playlist_id: str,
        track_uris: List[str],
        playlist_reader: IPlaylistReader,
        playlist_writer: IPlaylistWriter,
        track_writer: ITrackWriter,
    ) -> int:
        """Append tracks to the playlist."""
        logger.info(f"Appending {len(track_uris)} tracks to playlist {playlist_id}")

        # Get existing track URIs to avoid duplicates
        existing_uris = set()
        result = playlist_reader.playlist_tracks(playlist_id)

        while result:
            items = result.get("items", [])
            for item in items:
                if item.get("track"):
                    existing_uris.add(item["track"]["uri"])
            result = playlist_reader.next(result) if result.get("next") else None

        # Filter out duplicates
        new_tracks = [uri for uri in track_uris if uri not in existing_uris]

        if not new_tracks:
            logger.info("No new tracks to add (all already exist)")
            return 0

        logger.info(
            f"Adding {len(new_tracks)} new tracks (skipping {len(track_uris) - len(new_tracks)} duplicates)"
        )

        # Add new tracks in batches
        added_count = 0
        batch_size = 100

        for i in range(0, len(new_tracks), batch_size):
            batch = new_tracks[i : i + batch_size]
            try:
                track_writer.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                logger.debug(f"Added batch of {len(batch)} tracks")
            except Exception as e:
                logger.error(f"Failed to add batch: {e}")

        return added_count


class UpdateStrategyFactory:
    """Factory for creating playlist update strategies."""

    @staticmethod
    def create(mode: str) -> IPlaylistUpdateStrategy:
        """
        Create strategy based on update mode.

        Args:
            mode: Update mode ('replace' or 'append')

        Returns:
            Appropriate strategy instance

        Raises:
            ValueError: If mode is not recognized
        """
        strategies = {"replace": ReplaceStrategy(), "append": AppendStrategy()}

        strategy = strategies.get(mode.lower())
        if not strategy:
            raise ValueError(f"Unknown update mode: {mode}. Must be 'replace' or 'append'")

        return strategy
