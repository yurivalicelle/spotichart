"""
Data Transfer Objects (DTOs)

Immutable objects for transferring data between layers.
Provide clear contracts and type safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from ..core.models import Track


@dataclass(frozen=True)
class CreatePlaylistRequest:
    """Request to create a playlist."""

    name: str
    track_ids: List[str]
    description: str = ""
    public: bool = False
    update_mode: str = "replace"
    region: str = ""


@dataclass(frozen=True)
class CreatePlaylistResponse:
    """Response from playlist creation."""

    playlist_url: str
    tracks_added: int
    tracks_failed: int
    was_updated: bool
    errors: List[str] = field(default_factory=list)
    playlist_id: str = ""
    playlist_name: str = ""


@dataclass(frozen=True)
class ScrapedChartDTO:
    """DTO for scraped chart data."""

    region: str
    tracks: List[Track]
    scraped_at: datetime
    total_tracks: int

    @property
    def track_ids(self) -> List[str]:
        """Get list of track IDs."""
        return [track.id for track in self.tracks]


@dataclass(frozen=True)
class PlaylistListItem:
    """Single playlist in a list."""

    id: str
    name: str
    track_count: int
    public: bool
    url: str
    description: str = ""


@dataclass(frozen=True)
class PlaylistListResponse:
    """Response for playlist listing."""

    playlists: List[PlaylistListItem]
    total_count: int


@dataclass(frozen=True)
class RegionInfo:
    """Information about a chart region."""

    name: str
    display_name: str
    url: str


@dataclass(frozen=True)
class RegionListResponse:
    """Response for region listing."""

    regions: List[RegionInfo]


@dataclass(frozen=True)
class ChartPreviewResponse:
    """Response for chart preview."""

    region: str
    tracks: List[Track]
    total_tracks: int
    preview_count: int
