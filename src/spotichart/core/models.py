"""
Domain Models and Value Objects

Immutable data structures representing core domain concepts.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Track:
    """Immutable representation of a music track."""

    id: str
    name: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    @property
    def uri(self) -> str:
        """Get Spotify URI for this track."""
        return f"spotify:track:{self.id}"

    def __str__(self) -> str:
        if self.name and self.artist:
            return f"{self.artist} - {self.name}"
        return self.id


@dataclass(frozen=True)
class PlaylistMetadata:
    """Immutable representation of playlist metadata."""

    name: str
    description: str
    public: bool = False
    collaborative: bool = False

    def with_description(self, description: str) -> "PlaylistMetadata":
        """Create a new instance with updated description."""
        return PlaylistMetadata(
            name=self.name,
            description=description,
            public=self.public,
            collaborative=self.collaborative,
        )

    def with_visibility(self, public: bool) -> "PlaylistMetadata":
        """Create a new instance with updated visibility."""
        return PlaylistMetadata(
            name=self.name,
            description=self.description,
            public=public,
            collaborative=self.collaborative,
        )


@dataclass(frozen=True)
class ChartEntry:
    """Immutable representation of a chart entry."""

    track_id: str
    position: int
    region: str

    def to_track(self) -> Track:
        """Convert to Track value object."""
        return Track(id=self.track_id)
