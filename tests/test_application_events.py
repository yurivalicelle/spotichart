"""Tests for Event System (Observer Pattern)."""

from unittest.mock import Mock

import pytest

from spotichart.application.events import (
    EventBus,
    IEventListener,
    LoggingEventListener,
    MetricsEventListener,
    PlaylistCreatedEvent,
    PlaylistUpdatedEvent,
    ScrapingCompletedEvent,
    ScrapingStartedEvent,
    TrackAddedEvent,
    TracksScrapedEvent,
    ValidationFailedEvent,
)
from spotichart.core.models import Track


class TestEvents:
    """Tests for Event classes."""

    def test_playlist_created_event(self):
        """Test PlaylistCreatedEvent creation."""
        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)

        assert event.playlist_id == "123"
        assert event.playlist_name == "Test"
        assert event.track_count == 50
        assert event.timestamp is not None

    def test_playlist_updated_event(self):
        """Test PlaylistUpdatedEvent creation."""
        event = PlaylistUpdatedEvent(
            playlist_id="123",
            playlist_name="Test",
            tracks_added=10,
            tracks_removed=5,
        )

        assert event.playlist_id == "123"
        assert event.tracks_added == 10
        assert event.tracks_removed == 5

    def test_scraping_started_event(self):
        """Test ScrapingStartedEvent creation."""
        event = ScrapingStartedEvent(region="brazil", limit=100)

        assert event.region == "brazil"
        assert event.limit == 100

    def test_scraping_completed_event(self):
        """Test ScrapingCompletedEvent creation."""
        event = ScrapingCompletedEvent(region="brazil", tracks_found=50, duration_seconds=2.5)

        assert event.region == "brazil"
        assert event.tracks_found == 50
        assert event.duration_seconds == 2.5

    def test_validation_failed_event(self):
        """Test ValidationFailedEvent creation."""
        event = ValidationFailedEvent(errors=["Error 1", "Error 2"], context="CreatePlaylist")

        assert len(event.errors) == 2
        assert event.context == "CreatePlaylist"

    def test_track_added_event(self):
        """Test TrackAddedEvent creation."""
        track = Track(id="123", name="Song", artist="Artist")
        event = TrackAddedEvent(track=track, playlist_id="pl123", position=0)

        assert event.track == track
        assert event.playlist_id == "pl123"
        assert event.position == 0
        assert event.timestamp is not None

    def test_tracks_scraped_event(self):
        """Test TracksScrapedEvent creation."""
        event = TracksScrapedEvent(region="brazil", track_count=50, source="kworb")

        assert event.region == "brazil"
        assert event.track_count == 50
        assert event.source == "kworb"
        assert event.timestamp is not None


class TestEventBus:
    """Tests for EventBus."""

    def test_subscribe_and_publish(self):
        """Test subscribing and publishing events."""
        bus = EventBus()
        listener = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        listener.on_event.assert_called_once_with(event)

    def test_subscribe_multiple_listeners(self):
        """Test subscribing multiple listeners to same event."""
        bus = EventBus()
        listener1 = Mock(spec=IEventListener)
        listener2 = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener1)
        bus.subscribe(PlaylistCreatedEvent, listener2)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        listener1.on_event.assert_called_once()
        listener2.on_event.assert_called_once()

    def test_subscribe_different_events(self):
        """Test that listeners only receive subscribed events."""
        bus = EventBus()
        listener1 = Mock(spec=IEventListener)
        listener2 = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener1)
        bus.subscribe(ScrapingStartedEvent, listener2)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        listener1.on_event.assert_called_once()
        listener2.on_event.assert_not_called()

    def test_subscribe_all(self):
        """Test global subscription to all events."""
        bus = EventBus()
        global_listener = Mock(spec=IEventListener)

        bus.subscribe_all(global_listener)

        event1 = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        event2 = ScrapingStartedEvent(region="brazil", limit=100)

        bus.publish(event1)
        bus.publish(event2)

        assert global_listener.on_event.call_count == 2

    def test_unsubscribe(self):
        """Test unsubscribing listener."""
        bus = EventBus()
        listener = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener)
        bus.unsubscribe(PlaylistCreatedEvent, listener)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        listener.on_event.assert_not_called()

    def test_unsubscribe_not_subscribed(self):
        """Test unsubscribing listener that wasn't subscribed."""
        bus = EventBus()
        listener = Mock(spec=IEventListener)

        # Should not raise error
        bus.unsubscribe(PlaylistCreatedEvent, listener)

    def test_clear(self):
        """Test clearing all subscriptions."""
        bus = EventBus()
        listener1 = Mock(spec=IEventListener)
        listener2 = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener1)
        bus.subscribe_all(listener2)

        bus.clear()

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        listener1.on_event.assert_not_called()
        listener2.on_event.assert_not_called()

    def test_listener_error_doesnt_break_others(self):
        """Test that listener error doesn't prevent other listeners."""
        bus = EventBus()
        listener1 = Mock(spec=IEventListener)
        listener1.on_event.side_effect = Exception("Listener error")
        listener2 = Mock(spec=IEventListener)

        bus.subscribe(PlaylistCreatedEvent, listener1)
        bus.subscribe(PlaylistCreatedEvent, listener2)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        # Both should be called despite listener1 error
        listener1.on_event.assert_called_once()
        listener2.on_event.assert_called_once()


class TestLoggingEventListener:
    """Tests for LoggingEventListener."""

    def test_logs_event(self):
        """Test that events are logged."""
        mock_logger = Mock()
        listener = LoggingEventListener(logger_instance=mock_logger)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        listener.on_event(event)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "PlaylistCreatedEvent" in call_args

    def test_logs_different_events(self):
        """Test logging different event types."""
        mock_logger = Mock()
        listener = LoggingEventListener(logger_instance=mock_logger)

        events = [
            PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50),
            ScrapingStartedEvent(region="brazil", limit=100),
            ValidationFailedEvent(errors=["Error"], context="Test"),
        ]

        for event in events:
            listener.on_event(event)

        assert mock_logger.info.call_count == 3


class TestMetricsEventListener:
    """Tests for MetricsEventListener."""

    def test_initial_metrics(self):
        """Test that initial metrics are zero."""
        listener = MetricsEventListener()
        metrics = listener.get_metrics()

        assert metrics["playlists_created"] == 0
        assert metrics["playlists_updated"] == 0
        assert metrics["tracks_added"] == 0
        assert metrics["scrapes_completed"] == 0
        assert metrics["validation_failures"] == 0

    def test_playlist_created_increments_metrics(self):
        """Test that PlaylistCreatedEvent increments metrics."""
        listener = MetricsEventListener()

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        listener.on_event(event)

        metrics = listener.get_metrics()
        assert metrics["playlists_created"] == 1
        assert metrics["tracks_added"] == 50

    def test_playlist_updated_increments_metrics(self):
        """Test that PlaylistUpdatedEvent increments metrics."""
        listener = MetricsEventListener()

        event = PlaylistUpdatedEvent(
            playlist_id="123",
            playlist_name="Test",
            tracks_added=10,
            tracks_removed=5,
        )
        listener.on_event(event)

        metrics = listener.get_metrics()
        assert metrics["playlists_updated"] == 1
        assert metrics["tracks_added"] == 10

    def test_scraping_completed_increments_metrics(self):
        """Test that ScrapingCompletedEvent increments metrics."""
        listener = MetricsEventListener()

        event = ScrapingCompletedEvent(region="brazil", tracks_found=50, duration_seconds=2.5)
        listener.on_event(event)

        metrics = listener.get_metrics()
        assert metrics["scrapes_completed"] == 1

    def test_validation_failed_increments_metrics(self):
        """Test that ValidationFailedEvent increments metrics."""
        listener = MetricsEventListener()

        event = ValidationFailedEvent(errors=["Error"], context="Test")
        listener.on_event(event)

        metrics = listener.get_metrics()
        assert metrics["validation_failures"] == 1

    def test_multiple_events(self):
        """Test handling multiple events."""
        listener = MetricsEventListener()

        events = [
            PlaylistCreatedEvent(playlist_id="1", playlist_name="P1", track_count=50),
            PlaylistCreatedEvent(playlist_id="2", playlist_name="P2", track_count=30),
            PlaylistUpdatedEvent(
                playlist_id="1",
                playlist_name="P1",
                tracks_added=20,
                tracks_removed=0,
            ),
        ]

        for event in events:
            listener.on_event(event)

        metrics = listener.get_metrics()
        assert metrics["playlists_created"] == 2
        assert metrics["playlists_updated"] == 1
        assert metrics["tracks_added"] == 100  # 50 + 30 + 20

    def test_reset(self):
        """Test resetting metrics."""
        listener = MetricsEventListener()

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        listener.on_event(event)

        listener.reset()

        metrics = listener.get_metrics()
        assert metrics["playlists_created"] == 0
        assert metrics["tracks_added"] == 0

    def test_get_metrics_returns_copy(self):
        """Test that get_metrics returns a copy."""
        listener = MetricsEventListener()

        metrics1 = listener.get_metrics()
        metrics1["playlists_created"] = 999

        metrics2 = listener.get_metrics()
        assert metrics2["playlists_created"] == 0

    def test_ignores_unknown_events(self):
        """Test that unknown events don't cause errors."""
        listener = MetricsEventListener()

        event = ScrapingStartedEvent(region="brazil", limit=100)
        listener.on_event(event)  # Should not raise error

        metrics = listener.get_metrics()
        # Metrics should remain at zero since this event doesn't increment anything
        assert metrics["playlists_created"] == 0


class TestEventBusIntegration:
    """Integration tests for EventBus with real listeners."""

    def test_logging_and_metrics_together(self):
        """Test using logging and metrics listeners together."""
        bus = EventBus()
        mock_logger = Mock()

        logging_listener = LoggingEventListener(logger_instance=mock_logger)
        metrics_listener = MetricsEventListener()

        bus.subscribe_all(logging_listener)
        bus.subscribe_all(metrics_listener)

        event = PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50)
        bus.publish(event)

        # Logging listener should have logged
        mock_logger.info.assert_called_once()

        # Metrics listener should have recorded
        metrics = metrics_listener.get_metrics()
        assert metrics["playlists_created"] == 1
        assert metrics["tracks_added"] == 50

    def test_selective_subscription(self):
        """Test subscribing to specific events only."""
        bus = EventBus()
        listener1 = MetricsEventListener()
        listener2 = MetricsEventListener()

        # listener1 only listens to PlaylistCreatedEvent
        bus.subscribe(PlaylistCreatedEvent, listener1)

        # listener2 only listens to ScrapingCompletedEvent
        bus.subscribe(ScrapingCompletedEvent, listener2)

        bus.publish(PlaylistCreatedEvent(playlist_id="123", playlist_name="Test", track_count=50))
        bus.publish(ScrapingCompletedEvent(region="brazil", tracks_found=100, duration_seconds=2.0))

        # listener1 should only have PlaylistCreated metric
        metrics1 = listener1.get_metrics()
        assert metrics1["playlists_created"] == 1
        assert metrics1["scrapes_completed"] == 0

        # listener2 should only have ScrapeCompleted metric
        metrics2 = listener2.get_metrics()
        assert metrics2["playlists_created"] == 0
        assert metrics2["scrapes_completed"] == 1
