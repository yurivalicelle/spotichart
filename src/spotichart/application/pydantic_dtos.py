"""
Pydantic DTOs for Enhanced Validation

Using Pydantic for runtime type validation, automatic data validation,
and better error messages. This provides type safety beyond static analysis.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ..core.models import Track


# ============================================================================
# REQUEST DTOs (with validation)
# ============================================================================


class CreatePlaylistRequestV2(BaseModel):
    """
    Enhanced playlist creation request with Pydantic validation.

    Automatically validates:
    - Name length and format
    - Track IDs presence and format
    - Update mode values
    - Data types
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Playlist name (1-100 characters)",
        examples=["Top Brazil 2024", "Rock Classics"],
    )

    track_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="List of Spotify track IDs",
        examples=[["7ouMYWpwJ422jRcDASZB7P", "4cOdK2wGLETKBW3PvgPWqT"]],
    )

    description: str = Field(
        default="",
        max_length=300,
        description="Playlist description",
        examples=["My favorite tracks from Brazil"],
    )

    public: bool = Field(
        default=False,
        description="Whether the playlist is public",
        examples=[True, False],
    )

    update_mode: str = Field(
        default="replace",
        pattern="^(replace|append|new)$",
        description="How to handle existing playlists",
        examples=["replace", "append", "new"],
    )

    region: str = Field(
        default="",
        description="Chart region for tracking",
        examples=["brazil", "us", "global"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate playlist name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Playlist name cannot be empty or whitespace")
        return v.strip()

    @field_validator("track_ids")
    @classmethod
    def validate_track_ids(cls, v: List[str]) -> List[str]:
        """Validate track IDs are not empty."""
        if not v:
            raise ValueError("At least one track ID is required")

        for track_id in v:
            if not track_id or not track_id.strip():
                raise ValueError("Track IDs cannot be empty or whitespace")

        return v

    @field_validator("update_mode")
    @classmethod
    def validate_update_mode(cls, v: str) -> str:
        """Validate update mode is one of the allowed values."""
        allowed = {"replace", "append", "new"}
        if v not in allowed:
            raise ValueError(f"update_mode must be one of {allowed}, got '{v}'")
        return v

    class Config:
        """Pydantic configuration."""

        frozen = True  # Immutable
        str_strip_whitespace = True  # Auto-strip strings
        validate_assignment = True  # Validate on attribute assignment
        extra = "forbid"  # Reject extra fields


class ChartPreviewRequestV2(BaseModel):
    """Request to preview chart data."""

    region: str = Field(
        ...,
        min_length=1,
        description="Chart region to preview",
        examples=["brazil", "us", "global"],
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of tracks to preview",
        examples=[50, 100, 200],
    )

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region is not empty."""
        if not v or not v.strip():
            raise ValueError("Region cannot be empty")
        return v.strip().lower()

    class Config:
        """Pydantic configuration."""

        frozen = True
        str_strip_whitespace = True


# ============================================================================
# RESPONSE DTOs
# ============================================================================


class CreatePlaylistResponseV2(BaseModel):
    """Enhanced playlist creation response."""

    playlist_url: str = Field(
        ..., description="Spotify URL of the created playlist", examples=["https://open.spotify.com/playlist/abc123"]
    )

    playlist_id: str = Field(..., description="Spotify playlist ID", examples=["abc123"])

    playlist_name: str = Field(..., description="Name of the playlist", examples=["Top Brazil 2024"])

    tracks_added: int = Field(..., ge=0, description="Number of tracks successfully added", examples=[50])

    tracks_failed: int = Field(..., ge=0, description="Number of tracks that failed to add", examples=[0])

    was_updated: bool = Field(..., description="Whether an existing playlist was updated", examples=[False, True])

    errors: List[str] = Field(
        default_factory=list, description="List of error messages", examples=[[], ["Failed to add track xyz"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when response was created",
    )

    @model_validator(mode="after")
    def validate_track_counts(self):
        """Validate that track counts make sense."""
        if self.tracks_added < 0:
            raise ValueError("tracks_added cannot be negative")
        if self.tracks_failed < 0:
            raise ValueError("tracks_failed cannot be negative")
        if self.tracks_failed > 0 and not self.errors:
            raise ValueError("If tracks_failed > 0, errors list should not be empty")
        return self

    class Config:
        """Pydantic configuration."""

        frozen = True
        validate_assignment = True


class PlaylistStatisticsV2(BaseModel):
    """Playlist statistics with validation."""

    total_tracks: int = Field(..., ge=0, description="Total number of tracks")

    total_duration_ms: int = Field(..., ge=0, description="Total duration in milliseconds")

    total_duration_minutes: int = Field(..., ge=0, description="Total duration in minutes")

    explicit_tracks: int = Field(..., ge=0, description="Number of explicit tracks")

    unique_artists: int = Field(..., ge=0, description="Number of unique artists")

    average_duration_ms: int = Field(..., ge=0, description="Average track duration in milliseconds")

    @model_validator(mode="after")
    def validate_statistics(self):
        """Validate statistics consistency."""
        if self.explicit_tracks > self.total_tracks:
            raise ValueError("explicit_tracks cannot exceed total_tracks")
        if self.total_tracks > 0 and self.average_duration_ms == 0:
            raise ValueError("average_duration_ms should be > 0 when total_tracks > 0")
        return self

    class Config:
        """Pydantic configuration."""

        frozen = True


class TrackV2(BaseModel):
    """Enhanced Track model with Pydantic validation."""

    id: str = Field(..., min_length=1, description="Spotify track ID", examples=["7ouMYWpwJ422jRcDASZB7P"])

    name: Optional[str] = Field(None, description="Track name", examples=["Song Title"])

    artist: Optional[str] = Field(None, description="Artist name", examples=["Artist Name"])

    album: Optional[str] = Field(None, description="Album name", examples=["Album Title"])

    duration_ms: Optional[int] = Field(None, ge=0, description="Track duration in milliseconds")

    popularity: Optional[int] = Field(None, ge=0, le=100, description="Track popularity (0-100)")

    explicit: Optional[bool] = Field(None, description="Whether track has explicit content")

    @property
    def uri(self) -> str:
        """Get Spotify URI for this track."""
        return f"spotify:track:{self.id}"

    def __str__(self) -> str:
        """String representation."""
        if self.name and self.artist:
            return f"{self.artist} - {self.name}"
        return self.id

    class Config:
        """Pydantic configuration."""

        frozen = True
        str_strip_whitespace = True


# ============================================================================
# QUERY REQUEST DTOs
# ============================================================================


class SearchPlaylistsRequestV2(BaseModel):
    """Search playlists request with validation."""

    search_term: str = Field(..., min_length=1, description="Search term", examples=["rock", "brazil"])

    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")

    include_private: bool = Field(default=True, description="Include private playlists")

    @field_validator("search_term")
    @classmethod
    def validate_search_term(cls, v: str) -> str:
        """Validate search term."""
        if not v or not v.strip():
            raise ValueError("Search term cannot be empty")
        return v.strip().lower()

    class Config:
        """Pydantic configuration."""

        frozen = True
        str_strip_whitespace = True


# ============================================================================
# CONFIGURATION DTOs
# ============================================================================


class SpotifyCredentialsV2(BaseModel):
    """Spotify credentials with validation."""

    client_id: str = Field(..., min_length=32, max_length=32, description="Spotify Client ID")

    client_secret: str = Field(..., min_length=32, max_length=32, description="Spotify Client Secret")

    redirect_uri: str = Field(
        default="http://localhost:8888/callback",
        pattern=r"^https?://.*",
        description="OAuth redirect URI",
    )

    @field_validator("client_id", "client_secret")
    @classmethod
    def validate_credentials(cls, v: str) -> str:
        """Validate credentials are not placeholder values."""
        if v in ["your_client_id_here", "your_client_secret_here", ""]:
            raise ValueError("Please provide valid Spotify credentials")
        return v

    class Config:
        """Pydantic configuration."""

        frozen = True


class ApplicationConfigV2(BaseModel):
    """Application configuration with validation."""

    log_level: str = Field(
        default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Logging level"
    )

    cache_ttl_seconds: int = Field(
        default=300, ge=0, le=3600, description="Cache time-to-live in seconds"
    )

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")

    request_timeout: int = Field(default=30, ge=1, le=300, description="HTTP request timeout in seconds")

    enable_metrics: bool = Field(default=True, description="Enable metrics collection")

    enable_caching: bool = Field(default=True, description="Enable caching")

    class Config:
        """Pydantic configuration."""

        frozen = True
        validate_assignment = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def validate_and_convert(data: dict, model_class: type[BaseModel]) -> BaseModel:
    """
    Validate data against a Pydantic model.

    Args:
        data: Dictionary with data to validate
        model_class: Pydantic model class

    Returns:
        Validated model instance

    Raises:
        ValidationError: If validation fails
    """
    return model_class.model_validate(data)
