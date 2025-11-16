"""
Query Handlers (CQRS Read Side)

Handlers for read-only queries.
Optimized for reading data without side effects.
"""

import logging
import time
from typing import Dict, List, Optional

from ..core.chart_interfaces import IChartProvider
from ..core.interfaces import IPlaylistOperations, IPlaylistReader
from ..core.models import Track
from ..utils.exceptions import PlaylistNotFoundError
from ..utils.result import Failure, Result, Success
from .dtos import (
    ChartPreviewResponse,
    PlaylistListItem,
    PlaylistListResponse,
    RegionInfo,
    RegionListResponse,
)
from .events import EventBus, ScrapingCompletedEvent, ScrapingStartedEvent
from .queries import (
    GetPlaylistByIdQuery,
    GetPlaylistByNameQuery,
    GetPlaylistStatisticsQuery,
    GetPlaylistTracksQuery,
    IQueryHandler,
    ListPlaylistsQuery,
    ListRegionsQuery,
    PreviewChartsQuery,
    SearchPlaylistsQuery,
)

logger = logging.getLogger(__name__)


# ============================================================================
# PLAYLIST QUERY HANDLERS
# ============================================================================


class GetPlaylistByIdQueryHandler(IQueryHandler[Dict, Exception]):
    """Handler for getting a playlist by ID."""

    def __init__(self, playlist_reader: IPlaylistReader):
        """
        Initialize handler.

        Args:
            playlist_reader: Playlist reader for fetching data
        """
        self._playlist_reader = playlist_reader

    def handle(self, query: GetPlaylistByIdQuery) -> Result[Dict, Exception]:
        """
        Handle the query.

        Args:
            query: Query with playlist ID

        Returns:
            Result with playlist data or error
        """
        try:
            logger.debug(f"Fetching playlist by ID: {query.playlist_id}")

            # In a real CQRS system, this might query a read model
            # For now, we'll use the existing reader interface
            playlists = self._playlist_reader.current_user_playlists(limit=50)

            for playlist in playlists.get("items", []):
                if playlist["id"] == query.playlist_id:
                    return Success(playlist)

            error = PlaylistNotFoundError(f"Playlist not found: {query.playlist_id}")
            logger.warning(str(error))
            return Failure(error)

        except Exception as e:
            logger.exception(f"Error fetching playlist by ID: {e}")
            return Failure(e)


class GetPlaylistByNameQueryHandler(IQueryHandler[Optional[Dict], Exception]):
    """Handler for getting a playlist by name."""

    def __init__(self, playlist_ops: IPlaylistOperations):
        """
        Initialize handler.

        Args:
            playlist_ops: Playlist operations
        """
        self._playlist_ops = playlist_ops

    def handle(self, query: GetPlaylistByNameQuery) -> Result[Optional[Dict], Exception]:
        """
        Handle the query.

        Args:
            query: Query with playlist name

        Returns:
            Result with playlist data or None if not found
        """
        try:
            logger.debug(f"Fetching playlist by name: {query.name}")

            playlist = self._playlist_ops.find_by_name(query.name)

            return Success(playlist)

        except Exception as e:
            logger.exception(f"Error fetching playlist by name: {e}")
            return Failure(e)


class ListPlaylistsQueryHandler(IQueryHandler[PlaylistListResponse, Exception]):
    """Handler for listing user playlists."""

    def __init__(self, playlist_ops: IPlaylistOperations):
        """
        Initialize handler.

        Args:
            playlist_ops: Playlist operations
        """
        self._playlist_ops = playlist_ops

    def handle(self, query: ListPlaylistsQuery) -> Result[PlaylistListResponse, Exception]:
        """
        Handle the query.

        Args:
            query: Query with listing parameters

        Returns:
            Result with playlist list or error
        """
        try:
            logger.debug(f"Fetching up to {query.limit} playlists")

            playlists_data = self._playlist_ops.get_all(query.limit)

            playlists = [
                PlaylistListItem(
                    id=p["id"],
                    name=p["name"],
                    track_count=p["tracks"]["total"],
                    public=p["public"],
                    url=p["external_urls"]["spotify"],
                    description=p.get("description", ""),
                )
                for p in playlists_data
            ]

            return Success(PlaylistListResponse(playlists=playlists, total_count=len(playlists)))

        except Exception as e:
            logger.exception(f"Error listing playlists: {e}")
            return Failure(e)


class GetPlaylistTracksQueryHandler(IQueryHandler[List[Track], Exception]):
    """Handler for getting tracks from a playlist."""

    def __init__(self, playlist_reader: IPlaylistReader):
        """
        Initialize handler.

        Args:
            playlist_reader: Playlist reader for fetching data
        """
        self._playlist_reader = playlist_reader

    def handle(self, query: GetPlaylistTracksQuery) -> Result[List[Track], Exception]:
        """
        Handle the query.

        Args:
            query: Query with playlist ID

        Returns:
            Result with list of tracks or error
        """
        try:
            logger.debug(f"Fetching tracks from playlist: {query.playlist_id}")

            playlist_data = self._playlist_reader.playlist_tracks(query.playlist_id)

            tracks = []
            for item in playlist_data.get("items", []):
                track_data = item.get("track", {})
                if track_data:
                    track = Track(
                        id=track_data.get("id", ""),
                        name=track_data.get("name", ""),
                        artist=track_data.get("artists", [{}])[0].get("name", ""),
                        album=track_data.get("album", {}).get("name", ""),
                    )
                    tracks.append(track)

            return Success(tracks[: query.limit])

        except Exception as e:
            logger.exception(f"Error fetching playlist tracks: {e}")
            return Failure(e)


class SearchPlaylistsQueryHandler(IQueryHandler[PlaylistListResponse, Exception]):
    """Handler for searching playlists."""

    def __init__(self, playlist_ops: IPlaylistOperations):
        """
        Initialize handler.

        Args:
            playlist_ops: Playlist operations
        """
        self._playlist_ops = playlist_ops

    def handle(self, query: SearchPlaylistsQuery) -> Result[PlaylistListResponse, Exception]:
        """
        Handle the query.

        Args:
            query: Query with search parameters

        Returns:
            Result with matching playlists or error
        """
        try:
            logger.debug(f"Searching playlists: {query.search_term}")

            # Get all playlists and filter by search term
            all_playlists = self._playlist_ops.get_all(limit=100)

            search_term_lower = query.search_term.lower()
            filtered = [
                p
                for p in all_playlists
                if search_term_lower in p["name"].lower()
                or search_term_lower in p.get("description", "").lower()
            ]

            playlists = [
                PlaylistListItem(
                    id=p["id"],
                    name=p["name"],
                    track_count=p["tracks"]["total"],
                    public=p["public"],
                    url=p["external_urls"]["spotify"],
                    description=p.get("description", ""),
                )
                for p in filtered[: query.limit]
            ]

            return Success(PlaylistListResponse(playlists=playlists, total_count=len(playlists)))

        except Exception as e:
            logger.exception(f"Error searching playlists: {e}")
            return Failure(e)


class GetPlaylistStatisticsQueryHandler(IQueryHandler[Dict, Exception]):
    """Handler for getting playlist statistics."""

    def __init__(self, playlist_reader: IPlaylistReader):
        """
        Initialize handler.

        Args:
            playlist_reader: Playlist reader for fetching data
        """
        self._playlist_reader = playlist_reader

    def handle(self, query: GetPlaylistStatisticsQuery) -> Result[Dict, Exception]:
        """
        Handle the query.

        Args:
            query: Query with playlist ID

        Returns:
            Result with statistics or error
        """
        try:
            logger.debug(f"Calculating statistics for playlist: {query.playlist_id}")

            tracks_data = self._playlist_reader.playlist_tracks(query.playlist_id)
            items = tracks_data.get("items", [])

            # Calculate statistics
            total_tracks = len(items)
            total_duration_ms = sum(item.get("track", {}).get("duration_ms", 0) for item in items)
            explicit_count = sum(
                1 for item in items if item.get("track", {}).get("explicit", False)
            )

            # Get unique artists
            artists = set()
            for item in items:
                track = item.get("track", {})
                for artist in track.get("artists", []):
                    artists.add(artist.get("name", ""))

            statistics = {
                "total_tracks": total_tracks,
                "total_duration_ms": total_duration_ms,
                "total_duration_minutes": total_duration_ms // 60000,
                "explicit_tracks": explicit_count,
                "unique_artists": len(artists),
                "average_duration_ms": total_duration_ms // total_tracks if total_tracks > 0 else 0,
            }

            return Success(statistics)

        except Exception as e:
            logger.exception(f"Error calculating playlist statistics: {e}")
            return Failure(e)


# ============================================================================
# CHART QUERY HANDLERS
# ============================================================================


class ListRegionsQueryHandler(IQueryHandler[RegionListResponse, Exception]):
    """Handler for listing available chart regions."""

    def __init__(self, chart_provider: IChartProvider):
        """
        Initialize handler.

        Args:
            chart_provider: Chart provider to get regions from
        """
        self._chart_provider = chart_provider

    def handle(self, query: ListRegionsQuery) -> Result[RegionListResponse, Exception]:
        """
        Handle the query.

        Args:
            query: Query (no parameters needed)

        Returns:
            Result with region list or error
        """
        try:
            logger.debug("Fetching available regions")

            region_names = self._chart_provider.get_available_regions()

            regions = [
                RegionInfo(
                    name=region,
                    display_name=region.replace("-", " ").title(),
                    url=f"https://kworb.net/spotify/{region}.html",
                )
                for region in region_names
            ]

            return Success(RegionListResponse(regions=regions))

        except Exception as e:
            logger.exception(f"Error listing regions: {e}")
            return Failure(e)


class PreviewChartsQueryHandler(IQueryHandler[ChartPreviewResponse, Exception]):
    """Handler for previewing charts without creating playlist."""

    def __init__(self, chart_provider: IChartProvider, event_bus: EventBus = None):
        """
        Initialize handler.

        Args:
            chart_provider: Provider to scrape charts
            event_bus: Optional event bus
        """
        self._chart_provider = chart_provider
        self._event_bus = event_bus or EventBus()

    def handle(self, query: PreviewChartsQuery) -> Result[ChartPreviewResponse, Exception]:
        """
        Handle the query.

        Args:
            query: Query with preview parameters

        Returns:
            Result with preview response or error
        """
        try:
            logger.info(f"Previewing {query.region} charts (limit: {query.limit})")

            self._event_bus.publish(ScrapingStartedEvent(region=query.region, limit=query.limit))

            start_time = time.time()
            result = self._chart_provider.get_charts(query.region, query.limit)

            if result.is_failure():
                error = result.error
                logger.error(f"Failed to scrape charts: {error}")
                return Failure(error)

            tracks = result.unwrap()
            duration = time.time() - start_time

            self._event_bus.publish(
                ScrapingCompletedEvent(
                    region=query.region,
                    tracks_found=len(tracks),
                    duration_seconds=duration,
                )
            )

            return Success(
                ChartPreviewResponse(
                    region=query.region,
                    tracks=tracks,
                    total_tracks=len(tracks),
                    preview_count=min(len(tracks), query.limit),
                )
            )

        except Exception as e:
            logger.exception(f"Error previewing charts: {e}")
            return Failure(e)
