"""Test application layer imports."""


def test_import_commands():
    """Test importing command classes."""
    from spotichart.application import (
        CreatePlaylistCommand,
        ListPlaylistsCommand,
        ListRegionsCommand,
        PreviewChartsCommand,
    )

    assert CreatePlaylistCommand is not None
    assert PreviewChartsCommand is not None
    assert ListPlaylistsCommand is not None
    assert ListRegionsCommand is not None


def test_import_handlers():
    """Test importing handler classes."""
    from spotichart.application import (
        CreatePlaylistHandler,
        ListPlaylistsHandler,
        ListRegionsHandler,
        PreviewChartsHandler,
    )

    assert CreatePlaylistHandler is not None
    assert PreviewChartsHandler is not None
    assert ListPlaylistsHandler is not None
    assert ListRegionsHandler is not None


def test_import_dtos():
    """Test importing DTO classes."""
    from spotichart.application import (
        ChartPreviewResponse,
        CreatePlaylistRequest,
        CreatePlaylistResponse,
        PlaylistListItem,
        PlaylistListResponse,
        RegionInfo,
        RegionListResponse,
        ScrapedChartDTO,
    )

    assert CreatePlaylistRequest is not None
    assert CreatePlaylistResponse is not None
    assert ScrapedChartDTO is not None
    assert ChartPreviewResponse is not None
    assert PlaylistListItem is not None
    assert PlaylistListResponse is not None
    assert RegionInfo is not None
    assert RegionListResponse is not None


def test_import_events():
    """Test importing event classes."""
    from spotichart.application import (
        EventBus,
        IEventListener,
        LoggingEventListener,
        MetricsEventListener,
        PlaylistCreatedEvent,
        PlaylistUpdatedEvent,
        ScrapingCompletedEvent,
        ScrapingStartedEvent,
        ValidationFailedEvent,
    )

    assert EventBus is not None
    assert IEventListener is not None
    assert LoggingEventListener is not None
    assert MetricsEventListener is not None
    assert PlaylistCreatedEvent is not None
    assert PlaylistUpdatedEvent is not None
    assert ScrapingStartedEvent is not None
    assert ScrapingCompletedEvent is not None
    assert ValidationFailedEvent is not None


def test_import_services():
    """Test importing service classes."""
    from spotichart.application import PlaylistApplicationService

    assert PlaylistApplicationService is not None


def test_import_validators():
    """Test importing validator classes."""
    from spotichart.application import PlaylistRequestValidator, ValidationError

    assert PlaylistRequestValidator is not None
    assert ValidationError is not None
