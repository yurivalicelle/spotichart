"""
Query Objects (CQRS Read Side)

Read-only queries that don't modify state.
Separate from commands to follow CQRS pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from ..utils.result import Result

# Generic types for query handlers
TResponse = TypeVar("TResponse")
TError = TypeVar("TError")


class IQuery(ABC):
    """Base interface for queries (read operations)."""

    pass


class IQueryHandler(ABC, Generic[TResponse, TError]):
    """
    Base interface for query handlers.

    Query handlers are read-only operations that fetch data
    without modifying system state.
    """

    @abstractmethod
    def handle(self, query: IQuery) -> Result[TResponse, TError]:
        """
        Handle the query and return result.

        Args:
            query: Query object with parameters

        Returns:
            Result with data or error
        """
        pass


# ============================================================================
# QUERY DEFINITIONS
# ============================================================================


@dataclass(frozen=True)
class GetPlaylistByIdQuery(IQuery):
    """Query to get a single playlist by ID."""

    playlist_id: str


@dataclass(frozen=True)
class GetPlaylistByNameQuery(IQuery):
    """Query to get a playlist by name."""

    name: str


@dataclass(frozen=True)
class ListPlaylistsQuery(IQuery):
    """Query to list user's playlists."""

    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class ListRegionsQuery(IQuery):
    """Query to list available chart regions."""

    pass


@dataclass(frozen=True)
class PreviewChartsQuery(IQuery):
    """Query to preview chart data without creating playlist."""

    region: str
    limit: int = 50


@dataclass(frozen=True)
class GetPlaylistTracksQuery(IQuery):
    """Query to get tracks from a playlist."""

    playlist_id: str
    limit: int = 100


@dataclass(frozen=True)
class SearchPlaylistsQuery(IQuery):
    """Query to search playlists by criteria."""

    search_term: str
    limit: int = 20


@dataclass(frozen=True)
class GetPlaylistStatisticsQuery(IQuery):
    """Query to get statistics about a playlist."""

    playlist_id: str
