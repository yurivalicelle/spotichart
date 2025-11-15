# New SOLID architecture
from .chart_interfaces import IChartParser, IChartProvider, IHttpClient, IRegionUrlMapper
from .factory import SpotifyServiceFactory
from .http_client import RetryHttpClient
from .kworb_parser import KworbChartParser
from .kworb_provider import KworbChartProvider, KworbUrlMapper
from .models import ChartEntry, PlaylistMetadata, Track
from .repositories import CachedPlaylistRepository, IPlaylistRepository

# Legacy scraper (backward compatibility)
from .scraper import KworbScraper
from .strategies import (
    AppendStrategy,
    IPlaylistUpdateStrategy,
    ReplaceStrategy,
    UpdateStrategyFactory,
)

__all__ = [
    # Factory
    "SpotifyServiceFactory",
    # Legacy
    "KworbScraper",
    # Models
    "Track",
    "PlaylistMetadata",
    "ChartEntry",
    # Chart Interfaces
    "IChartProvider",
    "IChartParser",
    "IHttpClient",
    "IRegionUrlMapper",
    # Chart Implementations
    "KworbChartProvider",
    "KworbChartParser",
    "KworbUrlMapper",
    "RetryHttpClient",
    # Repository Pattern
    "IPlaylistRepository",
    "CachedPlaylistRepository",
    # Strategy Pattern
    "IPlaylistUpdateStrategy",
    "ReplaceStrategy",
    "AppendStrategy",
    "UpdateStrategyFactory",
]
