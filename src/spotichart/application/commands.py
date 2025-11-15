"""
Command Pattern Implementation

Commands represent user intentions/actions.
They are immutable and contain all data needed for execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ..utils.result import Result

T = TypeVar("T")
E = TypeVar("E")


class ICommand(ABC):
    """Base interface for all commands."""

    pass


class ICommandHandler(ABC, Generic[T, E]):
    """Base interface for command handlers."""

    @abstractmethod
    def handle(self, command: ICommand) -> Result[T, E]:
        """
        Handle the command and return a result.

        Args:
            command: The command to handle

        Returns:
            Result with success value or error
        """
        pass


@dataclass(frozen=True)
class CreatePlaylistCommand(ICommand):
    """Command to create or update a playlist from charts."""

    region: str
    limit: int
    name: str
    public: bool
    update_mode: str
    description: str = ""


@dataclass(frozen=True)
class PreviewChartsCommand(ICommand):
    """Command to preview charts without creating playlist."""

    region: str
    limit: int


@dataclass(frozen=True)
class ListPlaylistsCommand(ICommand):
    """Command to list user's playlists."""

    limit: int = 50


@dataclass(frozen=True)
class ListRegionsCommand(ICommand):
    """Command to list available regions."""

    pass
