"""
Application Layer

Contains application services, commands, DTOs, and validators.
Orchestrates domain logic without containing business rules.
"""

from .commands import (
    CreatePlaylistCommand,
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
    IEventListener,
    LoggingEventListener,
    MetricsEventListener,
    PlaylistCreatedEvent,
    PlaylistUpdatedEvent,
    ScrapingCompletedEvent,
    ScrapingStartedEvent,
    ValidationFailedEvent,
)
from .handlers import (
    CreatePlaylistHandler,
    ListPlaylistsHandler,
    ListRegionsHandler,
    PreviewChartsHandler,
)
from .services import PlaylistApplicationService
from .validators import PlaylistRequestValidator, ValidationError

__all__ = [
    # Commands
    "CreatePlaylistCommand",
    "PreviewChartsCommand",
    "ListPlaylistsCommand",
    "ListRegionsCommand",
    # Handlers
    "CreatePlaylistHandler",
    "PreviewChartsHandler",
    "ListPlaylistsHandler",
    "ListRegionsHandler",
    # DTOs
    "CreatePlaylistRequest",
    "CreatePlaylistResponse",
    "ScrapedChartDTO",
    "ChartPreviewResponse",
    "PlaylistListItem",
    "PlaylistListResponse",
    "RegionInfo",
    "RegionListResponse",
    # Events
    "EventBus",
    "IEventListener",
    "LoggingEventListener",
    "MetricsEventListener",
    "PlaylistCreatedEvent",
    "PlaylistUpdatedEvent",
    "ScrapingStartedEvent",
    "ScrapingCompletedEvent",
    "ValidationFailedEvent",
    # Services
    "PlaylistApplicationService",
    # Validators
    "PlaylistRequestValidator",
    "ValidationError",
]
