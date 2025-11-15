from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

class EventType(Enum):
    PLAYLIST_CREATED = auto()
    PLAYLIST_UPDATED = auto()
    TRACK_ADDED = auto()
    SCRAPING_STARTED = auto()
    SCRAPING_COMPLETED = auto()

@dataclass(frozen=True)
class Event:
    event_type: EventType
    data: dict
    timestamp: datetime = field(default_factory=datetime.now)

class EventManager:
    def __init__(self):
        self._listeners = defaultdict(list)

    def subscribe(self, event_type: EventType, callback) -> bool:
        self._listeners[event_type].append(callback)
        return True

    def unsubscribe(self, event_type: EventType, callback) -> bool:
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
            return True
        return False

    def publish(self, event: Event):
        for callback in self._listeners[event.event_type]:
            callback(event)

    def clear_all(self):
        self._listeners.clear()
