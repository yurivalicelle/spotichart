"""Tests for plugin system and event system."""

import pytest
from spotichart.plugins.plugin_interface import IPlugin, PluginMetadata
from spotichart.plugins.plugin_manager import PluginManager
from spotichart.events.event_manager import EventManager, Event, EventType


# ============================================================================
# Plugin System Tests
# ============================================================================

class SamplePlugin(IPlugin):
    """Sample plugin implementation for testing."""

    def __init__(self, name="test_plugin"):
        self._metadata = PluginMetadata(
            name=name,
            version="1.0.0",
            author="Test Author"
        )
        self.initialized = False
        self.shutdown_called = False

    @property
    def metadata(self):
        return self._metadata

    def initialize(self):
        self.initialized = True

    def shutdown(self):
        self.shutdown_called = True


class TestPluginMetadata:
    """Test PluginMetadata."""

    def test_create_metadata(self):
        """Create plugin metadata."""
        metadata = PluginMetadata(
            name="test",
            version="1.0.0",
            author="Author"
        )

        assert metadata.name == "test"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Author"


class TestIPlugin:
    """Test IPlugin interface."""

    def test_plugin_has_metadata(self):
        """Plugin has metadata property."""
        plugin = SamplePlugin()

        assert plugin.metadata is not None
        assert plugin.metadata.name == "test_plugin"

    def test_plugin_lifecycle(self):
        """Plugin lifecycle methods work."""
        plugin = SamplePlugin()

        assert plugin.initialized is False
        plugin.initialize()
        assert plugin.initialized is True

        assert plugin.shutdown_called is False
        plugin.shutdown()
        assert plugin.shutdown_called is True


class TestPluginManager:
    """Test PluginManager."""

    def test_singleton(self):
        """PluginManager is singleton."""
        manager1 = PluginManager.get_instance()
        manager2 = PluginManager.get_instance()

        assert manager1 is manager2

    def test_register_plugin(self):
        """Register plugin."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()  # Reset

        plugin = SamplePlugin("my_plugin")
        result = manager.register_plugin(plugin)

        assert result is True
        assert "my_plugin" in manager._plugins

    def test_register_duplicate_plugin(self):
        """Cannot register duplicate plugin."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        plugin1 = SamplePlugin("duplicate")
        plugin2 = SamplePlugin("duplicate")

        manager.register_plugin(plugin1)
        result = manager.register_plugin(plugin2)

        assert result is False

    def test_get_plugin(self):
        """Get registered plugin."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        plugin = SamplePlugin("findme")
        manager.register_plugin(plugin)

        found = manager.get_plugin("findme")

        assert found is not None
        assert found.metadata.name == "findme"

    def test_get_nonexistent_plugin(self):
        """Get nonexistent plugin returns None."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        found = manager.get_plugin("doesnotexist")

        assert found is None

    def test_initialize_all(self):
        """Initialize all plugins."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        plugin1 = SamplePlugin("plugin1")
        plugin2 = SamplePlugin("plugin2")

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        manager.initialize_all()

        assert plugin1.initialized is True
        assert plugin2.initialized is True

    def test_shutdown_all(self):
        """Shutdown all plugins."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        plugin1 = SamplePlugin("plugin1")
        plugin2 = SamplePlugin("plugin2")

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        manager.shutdown_all()

        assert plugin1.shutdown_called is True
        assert plugin2.shutdown_called is True

    def test_list_plugins(self):
        """List all registered plugins."""
        manager = PluginManager.get_instance()
        manager._plugins.clear()

        plugin1 = SamplePlugin("plugin1")
        plugin2 = SamplePlugin("plugin2")

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        plugins = manager.list_plugins()

        assert len(plugins) == 2
        assert "plugin1" in plugins
        assert "plugin2" in plugins


# ============================================================================
# Event System Tests
# ============================================================================

class TestEvent:
    """Test Event class."""

    def test_create_event(self):
        """Create event with data."""
        event = Event(
            event_type=EventType.PLAYLIST_CREATED,
            data={'playlist_id': '123'}
        )

        assert event.event_type == EventType.PLAYLIST_CREATED
        assert event.data['playlist_id'] == '123'
        assert event.timestamp is not None

    def test_event_immutable(self):
        """Event data should be immutable."""
        event = Event(
            event_type=EventType.TRACK_ADDED,
            data={'track_id': '456'}
        )

        # Can access data
        assert event.data['track_id'] == '456'
        assert event.event_type == EventType.TRACK_ADDED


class TestEventType:
    """Test EventType enum."""

    def test_has_expected_types(self):
        """EventType has expected event types."""
        expected_types = [
            'PLAYLIST_CREATED',
            'PLAYLIST_UPDATED',
            'TRACK_ADDED',
            'SCRAPING_STARTED',
            'SCRAPING_COMPLETED'
        ]

        for event_type_name in expected_types:
            assert hasattr(EventType, event_type_name)


class TestEventManager:
    """Test EventManager."""

    def test_subscribe(self):
        """Subscribe to event type."""
        manager = EventManager()
        callback = lambda event: None

        result = manager.subscribe(EventType.PLAYLIST_CREATED, callback)

        assert result is True

    def test_unsubscribe(self):
        """Unsubscribe from event type."""
        manager = EventManager()
        callback = lambda event: None

        manager.subscribe(EventType.PLAYLIST_CREATED, callback)
        result = manager.unsubscribe(EventType.PLAYLIST_CREATED, callback)

        assert result is True

    def test_unsubscribe_nonexistent(self):
        """Unsubscribe nonexistent listener returns False."""
        manager = EventManager()
        callback = lambda event: None

        result = manager.unsubscribe(EventType.PLAYLIST_CREATED, callback)

        assert result is False

    def test_publish_calls_subscribers(self):
        """Publish calls all subscribers."""
        manager = EventManager()

        calls = []

        def callback1(event):
            calls.append('callback1')

        def callback2(event):
            calls.append('callback2')

        manager.subscribe(EventType.PLAYLIST_CREATED, callback1)
        manager.subscribe(EventType.PLAYLIST_CREATED, callback2)

        event = Event(EventType.PLAYLIST_CREATED, data={'id': '123'})
        manager.publish(event)

        assert 'callback1' in calls
        assert 'callback2' in calls
        assert len(calls) == 2

    def test_publish_only_calls_matching_type(self):
        """Publish only calls subscribers of matching type."""
        manager = EventManager()

        created_calls = []
        updated_calls = []

        manager.subscribe(EventType.PLAYLIST_CREATED, lambda e: created_calls.append(1))
        manager.subscribe(EventType.PLAYLIST_UPDATED, lambda e: updated_calls.append(1))

        event = Event(EventType.PLAYLIST_CREATED, data={})
        manager.publish(event)

        assert len(created_calls) == 1
        assert len(updated_calls) == 0

    def test_publish_with_no_subscribers(self):
        """Publish with no subscribers doesn't crash."""
        manager = EventManager()

        event = Event(EventType.PLAYLIST_CREATED, data={})
        manager.publish(event)  # Should not raise

    def test_multiple_events(self):
        """Handle multiple events."""
        manager = EventManager()

        events_received = []

        def callback(event):
            events_received.append(event.event_type)

        manager.subscribe(EventType.PLAYLIST_CREATED, callback)
        manager.subscribe(EventType.PLAYLIST_UPDATED, callback)

        manager.publish(Event(EventType.PLAYLIST_CREATED, data={}))
        manager.publish(Event(EventType.PLAYLIST_UPDATED, data={}))

        assert EventType.PLAYLIST_CREATED in events_received
        assert EventType.PLAYLIST_UPDATED in events_received

    def test_clear_all_listeners(self):
        """Clear all listeners."""
        manager = EventManager()

        calls = []
        callback = lambda e: calls.append(1)

        manager.subscribe(EventType.PLAYLIST_CREATED, callback)
        manager.subscribe(EventType.TRACK_ADDED, callback)

        manager.clear_all()

        manager.publish(Event(EventType.PLAYLIST_CREATED, data={}))
        manager.publish(Event(EventType.TRACK_ADDED, data={}))

        assert len(calls) == 0
