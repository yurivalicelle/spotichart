"""
Observer Pattern - Event System

Decoupled event publishing and subscription.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Type

from ..core.models import Track

logger = logging.getLogger(__name__)


# ============================================================================
# Event Base Classes
# ============================================================================


class Event(ABC):
    """Base class for all events."""

    def __init__(self):
        self.timestamp = datetime.now()


# ============================================================================
# Domain Events
# ============================================================================


@dataclass
class PlaylistCreatedEvent(Event):
    """Event fired when a playlist is created."""

    playlist_id: str
    playlist_name: str
    track_count: int

    def __post_init__(self):
        super().__init__()


@dataclass
class PlaylistUpdatedEvent(Event):
    """Event fired when a playlist is updated."""

    playlist_id: str
    playlist_name: str
    tracks_added: int
    tracks_removed: int

    def __post_init__(self):
        super().__init__()


@dataclass
class TrackAddedEvent(Event):
    """Event fired when a track is added to playlist."""

    track: Track
    playlist_id: str
    position: int

    def __post_init__(self):
        super().__init__()


@dataclass
class TracksScrapedEvent(Event):
    """Event fired when tracks are scraped from charts."""

    region: str
    track_count: int
    source: str = "kworb"

    def __post_init__(self):
        super().__init__()


@dataclass
class ScrapingStartedEvent(Event):
    """Event fired when scraping starts."""

    region: str
    limit: int

    def __post_init__(self):
        super().__init__()


@dataclass
class ScrapingCompletedEvent(Event):
    """Event fired when scraping completes."""

    region: str
    tracks_found: int
    duration_seconds: float

    def __post_init__(self):
        super().__init__()


@dataclass
class ValidationFailedEvent(Event):
    """Event fired when validation fails."""

    errors: List[str]
    context: str = ""

    def __post_init__(self):
        super().__init__()


# ============================================================================
# Event Listener Interface
# ============================================================================


class IEventListener(ABC):
    """Interface for event listeners."""

    @abstractmethod
    def on_event(self, event: Event) -> None:
        """
        Handle an event.

        Args:
            event: The event to handle
        """
        pass


# ============================================================================
# Event Bus
# ============================================================================


class EventBus:
    """
    Event bus for publishing and subscribing to events.

    Implements Observer Pattern for decoupled event handling.
    """

    def __init__(self):
        """Initialize event bus."""
        self._listeners: Dict[Type[Event], List[IEventListener]] = {}
        self._global_listeners: List[IEventListener] = []

    def subscribe(self, event_type: Type[Event], listener: IEventListener) -> None:
        """
        Subscribe a listener to a specific event type.

        Args:
            event_type: Type of event to listen for
            listener: Listener to subscribe
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(listener)
        logger.debug(f"Subscribed {listener.__class__.__name__} to {event_type.__name__}")

    def subscribe_all(self, listener: IEventListener) -> None:
        """
        Subscribe a listener to all events.

        Args:
            listener: Listener to subscribe
        """
        self._global_listeners.append(listener)
        logger.debug(f"Subscribed {listener.__class__.__name__} to all events")

    def unsubscribe(self, event_type: Type[Event], listener: IEventListener) -> None:
        """
        Unsubscribe a listener from an event type.

        Args:
            event_type: Event type to unsubscribe from
            listener: Listener to unsubscribe
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(listener)
                logger.debug(
                    f"Unsubscribed {listener.__class__.__name__} from {event_type.__name__}"
                )
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed listeners.

        Args:
            event: Event to publish
        """
        event_type = type(event)
        logger.debug(f"Publishing event: {event_type.__name__}")

        # Notify specific listeners
        for listener in self._listeners.get(event_type, []):
            try:
                listener.on_event(event)
            except Exception as e:
                logger.error(f"Error in listener {listener.__class__.__name__}: {e}")

        # Notify global listeners
        for listener in self._global_listeners:
            try:
                listener.on_event(event)
            except Exception as e:
                logger.error(f"Error in global listener {listener.__class__.__name__}: {e}")

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._listeners.clear()
        self._global_listeners.clear()
        logger.debug("Cleared all event subscriptions")


# ============================================================================
# Built-in Listeners
# ============================================================================


class LoggingEventListener(IEventListener):
    """Listener that logs all events."""

    def __init__(self, logger_instance: logging.Logger = None):
        """
        Initialize logging listener.

        Args:
            logger_instance: Logger to use (defaults to module logger)
        """
        self.logger = logger_instance or logger

    def on_event(self, event: Event) -> None:
        """Log the event."""
        event_type = type(event).__name__
        self.logger.info(f"Event: {event_type} at {event.timestamp}")


class MetricsEventListener(IEventListener):
    """Listener that collects metrics from events."""

    def __init__(self):
        """Initialize metrics listener."""
        self.metrics: Dict[str, Any] = {
            "playlists_created": 0,
            "playlists_updated": 0,
            "tracks_added": 0,
            "scrapes_completed": 0,
            "validation_failures": 0,
        }

    def on_event(self, event: Event) -> None:
        """Update metrics based on event."""
        if isinstance(event, PlaylistCreatedEvent):
            self.metrics["playlists_created"] += 1
            self.metrics["tracks_added"] += event.track_count

        elif isinstance(event, PlaylistUpdatedEvent):
            self.metrics["playlists_updated"] += 1
            self.metrics["tracks_added"] += event.tracks_added

        elif isinstance(event, ScrapingCompletedEvent):
            self.metrics["scrapes_completed"] += 1

        elif isinstance(event, ValidationFailedEvent):
            self.metrics["validation_failures"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()

    def reset(self) -> None:
        """Reset all metrics."""
        for key in self.metrics:
            self.metrics[key] = 0
