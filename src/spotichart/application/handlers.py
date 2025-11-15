"""
Command Handlers

Implements command handlers that orchestrate business logic.
"""

import logging
import time
from datetime import datetime
from typing import List, Union

from ..core.chart_interfaces import IChartProvider
from ..core.interfaces import IPlaylistOperations, ITrackOperations, ITrackReader
from ..core.models import Track
from ..utils.exceptions import ChartScrapingError, ValidationError
from ..utils.result import Failure, Result, Success
from .commands import (
    CreatePlaylistCommand,
    ICommandHandler,
    ListPlaylistsCommand,
    ListRegionsCommand,
    PreviewChartsCommand,
)
from .dtos import (
    ChartPreviewResponse,
    CreatePlaylistRequest,
    CreatePlaylistResponse,
    PlaylistListItem,
    PlaylistListResponse,
    RegionInfo,
    RegionListResponse,
    ScrapedChartDTO,
)
from .events import (
    EventBus,
    PlaylistCreatedEvent,
    PlaylistUpdatedEvent,
    ScrapingCompletedEvent,
    ScrapingStartedEvent,
    ValidationFailedEvent,
)
from .validators import PlaylistRequestValidator

logger = logging.getLogger(__name__)


class CreatePlaylistHandler(
    ICommandHandler[CreatePlaylistResponse, Union[List[ValidationError], Exception]]
):
    """Handler for creating playlists from charts."""

    def __init__(
        self,
        chart_provider: IChartProvider,
        playlist_ops: IPlaylistOperations,
        track_ops: ITrackOperations,
        event_bus: EventBus = None,
        validator: PlaylistRequestValidator = None,
    ):
        """
        Initialize handler.

        Args:
            chart_provider: Provider to scrape charts
            playlist_ops: Playlist operations
            track_ops: Track operations
            event_bus: Optional event bus for publishing events
            validator: Optional validator (defaults to new instance)
        """
        self._chart_provider = chart_provider
        self._playlist_ops = playlist_ops
        self._track_ops = track_ops
        self._event_bus = event_bus or EventBus()
        self._validator = validator or PlaylistRequestValidator()

    def handle(
        self, command: CreatePlaylistCommand
    ) -> Result[CreatePlaylistResponse, Union[List[ValidationError], Exception]]:
        """
        Handle the create playlist command.

        Args:
            command: Command with playlist creation parameters

        Returns:
            Result with response or error
        """
        try:
            # Step 1: Scrape charts
            logger.info(f"Scraping {command.region} charts (limit: {command.limit})")
            self._event_bus.publish(
                ScrapingStartedEvent(region=command.region, limit=command.limit)
            )

            start_time = time.time()
            chart_result = self._chart_provider.get_charts(command.region, command.limit)

            if chart_result.is_failure():
                error = chart_result.error
                logger.error(f"Failed to scrape charts: {error}")
                return Failure(error)

            tracks = chart_result.unwrap()
            duration = time.time() - start_time

            self._event_bus.publish(
                ScrapingCompletedEvent(
                    region=command.region,
                    tracks_found=len(tracks),
                    duration_seconds=duration,
                )
            )

            if not tracks:
                error_msg = f"No tracks found for region: {command.region}"
                logger.warning(error_msg)
                return Failure(ChartScrapingError(error_msg))

            # Step 2: Build playlist request
            track_ids = [t.id for t in tracks if t.id]
            request = CreatePlaylistRequest(
                name=command.name,
                track_ids=track_ids,
                description=command.description,
                public=command.public,
                update_mode=command.update_mode,
                region=command.region,
            )

            # Step 3: Validate request
            validation_result = self._validator.validate(request)
            if validation_result.is_failure():
                errors = validation_result.error
                self._event_bus.publish(
                    ValidationFailedEvent(
                        errors=[str(e) for e in errors],
                        context="CreatePlaylist",
                    )
                )
                return Failure(errors)

            # Step 4: Create or update playlist
            return self._create_or_update_playlist(request)

        except Exception as e:
            logger.exception(f"Unexpected error in CreatePlaylistHandler: {e}")
            return Failure(e)

    def _create_or_update_playlist(
        self, request: CreatePlaylistRequest
    ) -> Result[CreatePlaylistResponse, Exception]:
        """Create or update playlist based on update mode."""
        try:
            # Find existing playlist
            existing = self._playlist_ops.find_by_name(request.name)

            if existing and request.update_mode == "new":
                # Force create new even if exists
                existing = None

            if existing:
                return self._update_existing_playlist(existing, request)
            else:
                return self._create_new_playlist(request)

        except Exception as e:
            logger.exception(f"Error creating/updating playlist: {e}")
            return Failure(e)

    def _create_new_playlist(
        self, request: CreatePlaylistRequest
    ) -> Result[CreatePlaylistResponse, Exception]:
        """Create a new playlist."""
        try:
            # Create playlist
            playlist = self._playlist_ops.create(
                name=request.name,
                description=request.description,
                public=request.public,
            )

            playlist_id = playlist["id"]
            playlist_url = playlist["external_urls"]["spotify"]

            # Add tracks
            tracks_added, tracks_failed, errors = self._add_tracks(playlist_id, request.track_ids)

            # Publish event
            self._event_bus.publish(
                PlaylistCreatedEvent(
                    playlist_id=playlist_id,
                    playlist_name=request.name,
                    track_count=tracks_added,
                )
            )

            logger.info(
                f"Created playlist: {request.name} ({tracks_added} tracks, {tracks_failed} failed)"
            )

            return Success(
                CreatePlaylistResponse(
                    playlist_url=playlist_url,
                    tracks_added=tracks_added,
                    tracks_failed=tracks_failed,
                    was_updated=False,
                    errors=errors,
                    playlist_id=playlist_id,
                    playlist_name=request.name,
                )
            )

        except Exception as e:
            logger.exception(f"Error creating new playlist: {e}")
            return Failure(e)

    def _update_existing_playlist(
        self, existing_playlist: dict, request: CreatePlaylistRequest
    ) -> Result[CreatePlaylistResponse, Exception]:
        """Update an existing playlist."""
        try:
            playlist_id = existing_playlist["id"]
            playlist_url = existing_playlist["external_urls"]["spotify"]

            # Update description
            self._playlist_ops.update_details(playlist_id, request.description)

            # Handle tracks based on update mode
            if request.update_mode == "replace":
                # Clear and re-add
                self._playlist_ops.clear(playlist_id)
                tracks_added, tracks_failed, errors = self._add_tracks(
                    playlist_id, request.track_ids
                )
            elif request.update_mode == "append":
                # Just add new tracks
                tracks_added, tracks_failed, errors = self._add_tracks(
                    playlist_id, request.track_ids
                )
            else:  # sync mode
                # Clear and re-add (same as replace for now)
                self._playlist_ops.clear(playlist_id)
                tracks_added, tracks_failed, errors = self._add_tracks(
                    playlist_id, request.track_ids
                )

            # Publish event
            self._event_bus.publish(
                PlaylistUpdatedEvent(
                    playlist_id=playlist_id,
                    playlist_name=request.name,
                    tracks_added=tracks_added,
                    tracks_removed=0,  # TODO: Track this properly
                )
            )

            logger.info(
                f"Updated playlist: {request.name} ({tracks_added} tracks, {tracks_failed} failed)"
            )

            return Success(
                CreatePlaylistResponse(
                    playlist_url=playlist_url,
                    tracks_added=tracks_added,
                    tracks_failed=tracks_failed,
                    was_updated=True,
                    errors=errors,
                    playlist_id=playlist_id,
                    playlist_name=request.name,
                )
            )

        except Exception as e:
            logger.exception(f"Error updating playlist: {e}")
            return Failure(e)

    def _add_tracks(self, playlist_id: str, track_ids: List[str]) -> tuple[int, int, List[str]]:
        """
        Add tracks to playlist.

        Returns:
            Tuple of (tracks_added, tracks_failed, error_messages)
        """
        if not track_ids:
            return 0, 0, []

        # Convert IDs to URIs
        track_uris = [self._track_ops.build_uri(tid) for tid in track_ids]

        try:
            # Add tracks in batches of 100 (Spotify API limit)
            batch_size = 100
            total_added = 0
            errors = []

            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i : i + batch_size]
                try:
                    self._track_ops.add_to_playlist(playlist_id, batch)
                    total_added += len(batch)
                except Exception as e:
                    error_msg = f"Failed to add batch {i // batch_size + 1}: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            tracks_failed = len(track_uris) - total_added

            return total_added, tracks_failed, errors

        except Exception as e:
            logger.exception(f"Error adding tracks: {e}")
            return 0, len(track_uris), [str(e)]


class PreviewChartsHandler(ICommandHandler[ChartPreviewResponse, Exception]):
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

    def handle(self, command: PreviewChartsCommand) -> Result[ChartPreviewResponse, Exception]:
        """
        Handle the preview charts command.

        Args:
            command: Command with preview parameters

        Returns:
            Result with preview response or error
        """
        try:
            logger.info(f"Previewing {command.region} charts (limit: {command.limit})")

            self._event_bus.publish(
                ScrapingStartedEvent(region=command.region, limit=command.limit)
            )

            start_time = time.time()
            result = self._chart_provider.get_charts(command.region, command.limit)

            if result.is_failure():
                error = result.error
                logger.error(f"Failed to scrape charts: {error}")
                return Failure(error)

            tracks = result.unwrap()
            duration = time.time() - start_time

            self._event_bus.publish(
                ScrapingCompletedEvent(
                    region=command.region,
                    tracks_found=len(tracks),
                    duration_seconds=duration,
                )
            )

            return Success(
                ChartPreviewResponse(
                    region=command.region,
                    tracks=tracks,
                    total_tracks=len(tracks),
                    preview_count=min(len(tracks), command.limit),
                )
            )

        except Exception as e:
            logger.exception(f"Error previewing charts: {e}")
            return Failure(e)


class ListPlaylistsHandler(ICommandHandler[PlaylistListResponse, Exception]):
    """Handler for listing user playlists."""

    def __init__(self, playlist_ops: IPlaylistOperations):
        """
        Initialize handler.

        Args:
            playlist_ops: Playlist operations
        """
        self._playlist_ops = playlist_ops

    def handle(self, command: ListPlaylistsCommand) -> Result[PlaylistListResponse, Exception]:
        """
        Handle the list playlists command.

        Args:
            command: Command with listing parameters

        Returns:
            Result with playlist list or error
        """
        try:
            logger.debug(f"Fetching up to {command.limit} playlists")

            playlists_data = self._playlist_ops.get_all(command.limit)

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


class ListRegionsHandler(ICommandHandler[RegionListResponse, Exception]):
    """Handler for listing available chart regions."""

    def __init__(self, chart_provider: IChartProvider):
        """
        Initialize handler.

        Args:
            chart_provider: Chart provider to get regions from
        """
        self._chart_provider = chart_provider

    def handle(self, command: ListRegionsCommand) -> Result[RegionListResponse, Exception]:
        """
        Handle the list regions command.

        Args:
            command: Command (no parameters needed)

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
