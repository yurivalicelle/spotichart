"""
Pipeline Pattern

Modular processing of data through composable steps.
"""

import logging
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from ..core.interfaces import ITrackReader
from ..core.models import Track
from .specifications import ISpecification, TrackIdValidSpecification

logger = logging.getLogger(__name__)

T = TypeVar("T")


class IPipelineStep(ABC, Generic[T]):
    """Base interface for pipeline steps."""

    @abstractmethod
    def process(self, items: List[T]) -> List[T]:
        """
        Process items.

        Args:
            items: Items to process

        Returns:
            Processed items
        """
        pass


class Pipeline(Generic[T]):
    """
    Pipeline for processing items through multiple steps.

    Implements Pipeline Pattern for modular data processing.
    """

    def __init__(self):
        """Initialize empty pipeline."""
        self._steps: List[IPipelineStep[T]] = []

    def add_step(self, step: IPipelineStep[T]) -> "Pipeline[T]":
        """
        Add a step to the pipeline.

        Args:
            step: Step to add

        Returns:
            Self for method chaining
        """
        self._steps.append(step)
        return self

    def execute(self, items: List[T]) -> List[T]:
        """
        Execute pipeline on items.

        Args:
            items: Items to process

        Returns:
            Processed items
        """
        result = items
        for step in self._steps:
            logger.debug(f"Executing step: {step.__class__.__name__}")
            result = step.process(result)
        return result

    def clear(self) -> "Pipeline[T]":
        """
        Clear all steps.

        Returns:
            Self for method chaining
        """
        self._steps.clear()
        return self


# ============================================================================
# Concrete Pipeline Steps for Tracks
# ============================================================================


class ValidateTrackStep(IPipelineStep[Track]):
    """Step that validates tracks."""

    def __init__(self, specification: ISpecification[Track] = None):
        """
        Initialize validation step.

        Args:
            specification: Specification to use (defaults to ID validation)
        """
        self.specification = specification or TrackIdValidSpecification()

    def process(self, tracks: List[Track]) -> List[Track]:
        """Validate and filter tracks."""
        valid_tracks = [t for t in tracks if self.specification.is_satisfied_by(t)]
        removed_count = len(tracks) - len(valid_tracks)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} invalid tracks")

        return valid_tracks


class RemoveDuplicatesStep(IPipelineStep[Track]):
    """Step that removes duplicate tracks."""

    def process(self, tracks: List[Track]) -> List[Track]:
        """Remove duplicates based on track ID."""
        seen = set()
        result = []

        for track in tracks:
            if track.id not in seen:
                seen.add(track.id)
                result.append(track)

        removed_count = len(tracks) - len(result)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate tracks")

        return result


class FilterBySpecificationStep(IPipelineStep[Track]):
    """Step that filters tracks using a specification."""

    def __init__(self, specification: ISpecification[Track]):
        """
        Initialize filter step.

        Args:
            specification: Specification to filter by
        """
        self.specification = specification

    def process(self, tracks: List[Track]) -> List[Track]:
        """Filter tracks using specification."""
        filtered = [t for t in tracks if self.specification.is_satisfied_by(t)]
        removed_count = len(tracks) - len(filtered)

        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} tracks")

        return filtered


class LimitTracksStep(IPipelineStep[Track]):
    """Step that limits number of tracks."""

    def __init__(self, limit: int):
        """
        Initialize limit step.

        Args:
            limit: Maximum number of tracks
        """
        self.limit = limit

    def process(self, tracks: List[Track]) -> List[Track]:
        """Limit tracks to specified count."""
        if len(tracks) > self.limit:
            logger.info(f"Limiting tracks from {len(tracks)} to {self.limit}")
            return tracks[: self.limit]
        return tracks


class EnrichTrackMetadataStep(IPipelineStep[Track]):
    """Step that enriches tracks with metadata from Spotify."""

    def __init__(self, track_reader: ITrackReader):
        """
        Initialize enrich step.

        Args:
            track_reader: Reader to fetch track metadata
        """
        self.track_reader = track_reader

    def process(self, tracks: List[Track]) -> List[Track]:
        """Enrich tracks with metadata."""
        enriched = []
        enriched_count = 0

        for track in tracks:
            # Skip if already has metadata
            if track.name and track.artist:
                enriched.append(track)
                continue

            # Fetch metadata
            metadata = self.track_reader.track(track.id)
            if metadata:
                enriched_track = Track(
                    id=track.id,
                    name=metadata.get("name"),
                    artist=(
                        metadata.get("artists", [{}])[0].get("name")
                        if metadata.get("artists")
                        else None
                    ),
                    album=metadata.get("album", {}).get("name") if metadata.get("album") else None,
                )
                enriched.append(enriched_track)
                enriched_count += 1
            else:
                enriched.append(track)

        if enriched_count > 0:
            logger.info(f"Enriched {enriched_count} tracks with metadata")

        return enriched


class SortTracksStep(IPipelineStep[Track]):
    """Step that sorts tracks."""

    def __init__(self, key_func=None, reverse: bool = False):
        """
        Initialize sort step.

        Args:
            key_func: Function to extract sort key (defaults to preserving order)
            reverse: Whether to reverse sort
        """
        self.key_func = key_func
        self.reverse = reverse

    def process(self, tracks: List[Track]) -> List[Track]:
        """Sort tracks."""
        if self.key_func:
            return sorted(tracks, key=self.key_func, reverse=self.reverse)
        return tracks  # Preserve order if no key function
