"""
Application Services

High-level services that orchestrate commands and handlers.
Provides a facade for the application layer.
"""

import logging
from typing import List, Union

from ..core.chart_interfaces import IChartProvider
from ..core.interfaces import IPlaylistOperations, ITrackOperations
from ..utils.exceptions import ValidationError
from ..utils.result import Result
from .commands import (
    CreatePlaylistCommand,
    ListPlaylistsCommand,
    ListRegionsCommand,
    PreviewChartsCommand,
)
from .dtos import (
    ChartPreviewResponse,
    CreatePlaylistResponse,
    PlaylistListResponse,
    RegionListResponse,
)
from .events import EventBus
from .handlers import (
    CreatePlaylistHandler,
    ListPlaylistsHandler,
    ListRegionsHandler,
    PreviewChartsHandler,
)

logger = logging.getLogger(__name__)


class PlaylistApplicationService:
    """
    Application service for playlist operations.

    Provides a high-level API for working with playlists and charts.
    Acts as a facade over the command/handler architecture.
    """

    def __init__(
        self,
        chart_provider: IChartProvider,
        playlist_ops: IPlaylistOperations,
        track_ops: ITrackOperations,
        event_bus: EventBus = None,
    ):
        """
        Initialize application service.

        Args:
            chart_provider: Chart data provider
            playlist_ops: Playlist operations
            track_ops: Track operations
            event_bus: Optional event bus (creates new if not provided)
        """
        self._chart_provider = chart_provider
        self._playlist_ops = playlist_ops
        self._track_ops = track_ops
        self._event_bus = event_bus or EventBus()

        # Initialize handlers
        self._create_playlist_handler = CreatePlaylistHandler(
            chart_provider=chart_provider,
            playlist_ops=playlist_ops,
            track_ops=track_ops,
            event_bus=self._event_bus,
        )

        self._preview_charts_handler = PreviewChartsHandler(
            chart_provider=chart_provider,
            event_bus=self._event_bus,
        )

        self._list_playlists_handler = ListPlaylistsHandler(playlist_ops=playlist_ops)

        self._list_regions_handler = ListRegionsHandler(chart_provider=chart_provider)

        logger.debug("PlaylistApplicationService initialized")

    def create_playlist_from_charts(
        self,
        region: str,
        limit: int,
        name: str,
        public: bool = False,
        update_mode: str = "replace",
        description: str = "",
    ) -> Result[CreatePlaylistResponse, Union[List[ValidationError], Exception]]:
        """
        Create or update a playlist from chart data.

        Args:
            region: Chart region (e.g., 'brazil', 'global', 'us')
            limit: Maximum number of tracks to include
            name: Playlist name
            public: Whether playlist should be public
            update_mode: How to handle existing playlist ('replace', 'append', 'new')
            description: Playlist description

        Returns:
            Result with response or error
        """
        command = CreatePlaylistCommand(
            region=region,
            limit=limit,
            name=name,
            public=public,
            update_mode=update_mode,
            description=description,
        )

        logger.info(
            f"Creating playlist from {region} charts: {name} (limit={limit}, mode={update_mode})"
        )

        return self._create_playlist_handler.handle(command)

    def preview_charts(
        self, region: str, limit: int = 50
    ) -> Result[ChartPreviewResponse, Exception]:
        """
        Preview chart data without creating a playlist.

        Args:
            region: Chart region
            limit: Maximum number of tracks to preview

        Returns:
            Result with preview response or error
        """
        command = PreviewChartsCommand(region=region, limit=limit)

        logger.info(f"Previewing {region} charts (limit={limit})")

        return self._preview_charts_handler.handle(command)

    def list_playlists(self, limit: int = 50) -> Result[PlaylistListResponse, Exception]:
        """
        List user's playlists.

        Args:
            limit: Maximum number of playlists to return

        Returns:
            Result with playlist list or error
        """
        command = ListPlaylistsCommand(limit=limit)

        logger.debug(f"Listing playlists (limit={limit})")

        return self._list_playlists_handler.handle(command)

    def list_available_regions(self) -> Result[RegionListResponse, Exception]:
        """
        List available chart regions.

        Returns:
            Result with region list or error
        """
        command = ListRegionsCommand()

        logger.debug("Listing available regions")

        return self._list_regions_handler.handle(command)

    def get_event_bus(self) -> EventBus:
        """
        Get the event bus for subscribing to events.

        Returns:
            EventBus instance
        """
        return self._event_bus

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._chart_provider.close()
            logger.debug("PlaylistApplicationService cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
