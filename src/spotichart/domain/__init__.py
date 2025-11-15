"""
Domain Layer

Contains domain logic, specifications, and business rules.
"""

from .builders import PlaylistBuilder, TrackCollectionBuilder
from .decorators import (
    CachingPlaylistDecorator,
    LoggingPlaylistDecorator,
    MetricsPlaylistDecorator,
    RetryPlaylistDecorator,
)
from .pipelines import (
    EnrichTrackMetadataStep,
    FilterBySpecificationStep,
    IPipelineStep,
    LimitTracksStep,
    Pipeline,
    RemoveDuplicatesStep,
    SortTracksStep,
    ValidateTrackStep,
)
from .specifications import (
    AlwaysFalseSpecification,
    AlwaysTrueSpecification,
    AndSpecification,
    ISpecification,
    NotSpecification,
    OrSpecification,
    TrackHasMetadataSpecification,
    TrackIdValidSpecification,
)

__all__ = [
    # Specifications
    "ISpecification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "TrackIdValidSpecification",
    "TrackHasMetadataSpecification",
    "AlwaysTrueSpecification",
    "AlwaysFalseSpecification",
    # Pipelines
    "IPipelineStep",
    "Pipeline",
    "ValidateTrackStep",
    "RemoveDuplicatesStep",
    "EnrichTrackMetadataStep",
    "FilterBySpecificationStep",
    "LimitTracksStep",
    "SortTracksStep",
    # Builders
    "PlaylistBuilder",
    "TrackCollectionBuilder",
    # Decorators
    "LoggingPlaylistDecorator",
    "MetricsPlaylistDecorator",
    "RetryPlaylistDecorator",
    "CachingPlaylistDecorator",
]
