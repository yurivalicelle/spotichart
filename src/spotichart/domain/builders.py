"""
Builder Pattern

Fluent API for constructing complex objects with validation.
"""

import logging
from typing import List, Optional

from ..application.dtos import CreatePlaylistRequest
from ..core.models import Track
from .pipelines import IPipelineStep, Pipeline
from .specifications import AlwaysTrueSpecification, ISpecification

logger = logging.getLogger(__name__)


class PlaylistBuilder:
    """
    Builder for creating playlist requests with fluent API.

    Implements Builder Pattern for constructing complex CreatePlaylistRequest objects.
    """

    def __init__(self):
        """Initialize builder with default values."""
        self._name: Optional[str] = None
        self._description: str = ""
        self._public: bool = False
        self._update_mode: str = "replace"
        self._region: str = ""
        self._track_ids: List[str] = []
        self._tracks: List[Track] = []
        self._specification: ISpecification[Track] = AlwaysTrueSpecification()
        self._pipeline: Optional[Pipeline[Track]] = None

    def with_name(self, name: str) -> "PlaylistBuilder":
        """
        Set playlist name.

        Args:
            name: Playlist name

        Returns:
            Self for method chaining
        """
        self._name = name
        return self

    def with_description(self, description: str) -> "PlaylistBuilder":
        """
        Set playlist description.

        Args:
            description: Playlist description

        Returns:
            Self for method chaining
        """
        self._description = description
        return self

    def with_public(self, public: bool = True) -> "PlaylistBuilder":
        """
        Set playlist visibility.

        Args:
            public: Whether playlist is public

        Returns:
            Self for method chaining
        """
        self._public = public
        return self

    def with_update_mode(self, mode: str) -> "PlaylistBuilder":
        """
        Set update mode.

        Args:
            mode: Update mode (replace, append, or sync)

        Returns:
            Self for method chaining
        """
        self._update_mode = mode
        return self

    def with_region(self, region: str) -> "PlaylistBuilder":
        """
        Set region for playlist.

        Args:
            region: Region code

        Returns:
            Self for method chaining
        """
        self._region = region
        return self

    def add_track_id(self, track_id: str) -> "PlaylistBuilder":
        """
        Add a single track ID.

        Args:
            track_id: Spotify track ID

        Returns:
            Self for method chaining
        """
        if track_id and track_id not in self._track_ids:
            self._track_ids.append(track_id)
        return self

    def add_track_ids(self, track_ids: List[str]) -> "PlaylistBuilder":
        """
        Add multiple track IDs.

        Args:
            track_ids: List of Spotify track IDs

        Returns:
            Self for method chaining
        """
        for track_id in track_ids:
            self.add_track_id(track_id)
        return self

    def add_track(self, track: Track) -> "PlaylistBuilder":
        """
        Add a single track.

        Args:
            track: Track to add

        Returns:
            Self for method chaining
        """
        if track and track.id:
            self._tracks.append(track)
        return self

    def add_tracks(self, tracks: List[Track]) -> "PlaylistBuilder":
        """
        Add multiple tracks.

        Args:
            tracks: List of tracks to add

        Returns:
            Self for method chaining
        """
        for track in tracks:
            self.add_track(track)
        return self

    def with_filter(self, specification: ISpecification[Track]) -> "PlaylistBuilder":
        """
        Set filter specification for tracks.

        Args:
            specification: Specification to filter tracks

        Returns:
            Self for method chaining
        """
        self._specification = specification
        return self

    def with_pipeline(self, pipeline: Pipeline[Track]) -> "PlaylistBuilder":
        """
        Set processing pipeline for tracks.

        Args:
            pipeline: Pipeline to process tracks

        Returns:
            Self for method chaining
        """
        self._pipeline = pipeline
        return self

    def add_pipeline_step(self, step: IPipelineStep[Track]) -> "PlaylistBuilder":
        """
        Add a step to the processing pipeline.

        Args:
            step: Pipeline step to add

        Returns:
            Self for method chaining
        """
        if self._pipeline is None:
            self._pipeline = Pipeline[Track]()
        self._pipeline.add_step(step)
        return self

    def build(self) -> CreatePlaylistRequest:
        """
        Build the playlist request.

        Returns:
            CreatePlaylistRequest with all configured values

        Raises:
            ValueError: If name is not set
        """
        if not self._name:
            raise ValueError("Playlist name is required")

        # Process tracks through specification filter
        filtered_tracks = [t for t in self._tracks if self._specification.is_satisfied_by(t)]

        if len(filtered_tracks) < len(self._tracks):
            removed = len(self._tracks) - len(filtered_tracks)
            logger.info(f"Builder filtered out {removed} tracks using specification")

        # Process tracks through pipeline if configured
        if self._pipeline:
            filtered_tracks = self._pipeline.execute(filtered_tracks)
            logger.info(f"Builder processed {len(filtered_tracks)} tracks through pipeline")

        # Extract track IDs from Track objects
        track_ids_from_tracks = [t.id for t in filtered_tracks if t.id]

        # Combine with explicitly added track IDs
        all_track_ids = list(dict.fromkeys(self._track_ids + track_ids_from_tracks))

        logger.debug(
            f"Building playlist request: name={self._name}, "
            f"tracks={len(all_track_ids)}, "
            f"public={self._public}, "
            f"mode={self._update_mode}"
        )

        return CreatePlaylistRequest(
            name=self._name,
            track_ids=all_track_ids,
            description=self._description,
            public=self._public,
            update_mode=self._update_mode,
            region=self._region,
        )

    def reset(self) -> "PlaylistBuilder":
        """
        Reset builder to initial state.

        Returns:
            Self for method chaining
        """
        self.__init__()
        return self


class TrackCollectionBuilder:
    """
    Builder for creating collections of tracks with processing.

    Useful for building filtered and processed track lists.
    """

    def __init__(self):
        """Initialize builder."""
        self._tracks: List[Track] = []
        self._specification: ISpecification[Track] = AlwaysTrueSpecification()
        self._pipeline: Optional[Pipeline[Track]] = None
        self._limit: Optional[int] = None

    def add_track(self, track: Track) -> "TrackCollectionBuilder":
        """
        Add a track to the collection.

        Args:
            track: Track to add

        Returns:
            Self for method chaining
        """
        if track:
            self._tracks.append(track)
        return self

    def add_tracks(self, tracks: List[Track]) -> "TrackCollectionBuilder":
        """
        Add multiple tracks.

        Args:
            tracks: Tracks to add

        Returns:
            Self for method chaining
        """
        self._tracks.extend(tracks)
        return self

    def with_filter(self, specification: ISpecification[Track]) -> "TrackCollectionBuilder":
        """
        Set filter specification.

        Args:
            specification: Specification to filter tracks

        Returns:
            Self for method chaining
        """
        self._specification = specification
        return self

    def with_pipeline(self, pipeline: Pipeline[Track]) -> "TrackCollectionBuilder":
        """
        Set processing pipeline.

        Args:
            pipeline: Pipeline to process tracks

        Returns:
            Self for method chaining
        """
        self._pipeline = pipeline
        return self

    def with_limit(self, limit: int) -> "TrackCollectionBuilder":
        """
        Set maximum number of tracks.

        Args:
            limit: Maximum tracks to return

        Returns:
            Self for method chaining
        """
        self._limit = limit
        return self

    def build(self) -> List[Track]:
        """
        Build the track collection.

        Returns:
            Processed and filtered list of tracks
        """
        # Filter tracks
        result = [t for t in self._tracks if self._specification.is_satisfied_by(t)]

        # Process through pipeline
        if self._pipeline:
            result = self._pipeline.execute(result)

        # Apply limit
        if self._limit is not None and len(result) > self._limit:
            result = result[: self._limit]

        logger.debug(f"Built track collection: input={len(self._tracks)}, output={len(result)}")

        return result
