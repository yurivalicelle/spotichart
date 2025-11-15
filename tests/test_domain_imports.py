"""Test domain layer imports."""


def test_import_specifications():
    """Test importing specification classes."""
    from spotichart.domain import (
        AlwaysFalseSpecification,
        AlwaysTrueSpecification,
        AndSpecification,
        ISpecification,
        NotSpecification,
        OrSpecification,
        TrackHasMetadataSpecification,
        TrackIdValidSpecification,
    )

    assert ISpecification is not None
    assert AndSpecification is not None
    assert OrSpecification is not None
    assert NotSpecification is not None
    assert TrackIdValidSpecification is not None
    assert TrackHasMetadataSpecification is not None
    assert AlwaysTrueSpecification is not None
    assert AlwaysFalseSpecification is not None


def test_import_pipelines():
    """Test importing pipeline classes."""
    from spotichart.domain import (
        EnrichTrackMetadataStep,
        FilterBySpecificationStep,
        IPipelineStep,
        LimitTracksStep,
        Pipeline,
        RemoveDuplicatesStep,
        SortTracksStep,
        ValidateTrackStep,
    )

    assert IPipelineStep is not None
    assert Pipeline is not None
    assert ValidateTrackStep is not None
    assert RemoveDuplicatesStep is not None
    assert EnrichTrackMetadataStep is not None
    assert FilterBySpecificationStep is not None
    assert LimitTracksStep is not None
    assert SortTracksStep is not None


def test_import_builders():
    """Test importing builder classes."""
    from spotichart.domain import PlaylistBuilder, TrackCollectionBuilder

    assert PlaylistBuilder is not None
    assert TrackCollectionBuilder is not None


def test_import_decorators():
    """Test importing decorator classes."""
    from spotichart.domain import (
        CachingPlaylistDecorator,
        LoggingPlaylistDecorator,
        MetricsPlaylistDecorator,
        RetryPlaylistDecorator,
    )

    assert LoggingPlaylistDecorator is not None
    assert MetricsPlaylistDecorator is not None
    assert RetryPlaylistDecorator is not None
    assert CachingPlaylistDecorator is not None
