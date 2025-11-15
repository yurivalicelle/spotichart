"""
Specification Pattern

Composable business rules for filtering and validation.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class ISpecification(ABC, Generic[T]):
    """Base interface for specifications."""

    @abstractmethod
    def is_satisfied_by(self, item: T) -> bool:
        """
        Check if item satisfies the specification.

        Args:
            item: Item to check

        Returns:
            True if specification is satisfied
        """
        pass

    def and_(self, other: "ISpecification[T]") -> "ISpecification[T]":
        """
        Combine with AND logic.

        Args:
            other: Other specification

        Returns:
            Combined specification
        """
        return AndSpecification(self, other)

    def or_(self, other: "ISpecification[T]") -> "ISpecification[T]":
        """
        Combine with OR logic.

        Args:
            other: Other specification

        Returns:
            Combined specification
        """
        return OrSpecification(self, other)

    def not_(self) -> "ISpecification[T]":
        """
        Negate this specification.

        Returns:
            Negated specification
        """
        return NotSpecification(self)


class AndSpecification(ISpecification[T]):
    """Specification that combines two specs with AND."""

    def __init__(self, left: ISpecification[T], right: ISpecification[T]):
        """
        Initialize AND specification.

        Args:
            left: Left specification
            right: Right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, item: T) -> bool:
        """Check if both specifications are satisfied."""
        return self.left.is_satisfied_by(item) and self.right.is_satisfied_by(item)


class OrSpecification(ISpecification[T]):
    """Specification that combines two specs with OR."""

    def __init__(self, left: ISpecification[T], right: ISpecification[T]):
        """
        Initialize OR specification.

        Args:
            left: Left specification
            right: Right specification
        """
        self.left = left
        self.right = right

    def is_satisfied_by(self, item: T) -> bool:
        """Check if either specification is satisfied."""
        return self.left.is_satisfied_by(item) or self.right.is_satisfied_by(item)


class NotSpecification(ISpecification[T]):
    """Specification that negates another spec."""

    def __init__(self, spec: ISpecification[T]):
        """
        Initialize NOT specification.

        Args:
            spec: Specification to negate
        """
        self.spec = spec

    def is_satisfied_by(self, item: T) -> bool:
        """Check if specification is NOT satisfied."""
        return not self.spec.is_satisfied_by(item)


# ============================================================================
# Concrete Specifications for Tracks
# ============================================================================


from ..core.models import Track


class TrackIdValidSpecification(ISpecification[Track]):
    """Specification for tracks with valid IDs."""

    def is_satisfied_by(self, track: Track) -> bool:
        """Check if track has a valid ID."""
        return track.id is not None and len(track.id.strip()) > 0


class TrackHasMetadataSpecification(ISpecification[Track]):
    """Specification for tracks with metadata."""

    def is_satisfied_by(self, track: Track) -> bool:
        """Check if track has name and artist."""
        return (
            track.name is not None
            and len(track.name.strip()) > 0
            and track.artist is not None
            and len(track.artist.strip()) > 0
        )


class AlwaysTrueSpecification(ISpecification[T]):
    """Specification that always returns True."""

    def is_satisfied_by(self, item: T) -> bool:
        """Always satisfied."""
        return True


class AlwaysFalseSpecification(ISpecification[T]):
    """Specification that always returns False."""

    def is_satisfied_by(self, item: T) -> bool:
        """Never satisfied."""
        return False
