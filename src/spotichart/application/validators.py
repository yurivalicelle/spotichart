"""
Validation Layer

Structured validation with clear error messages.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from ..utils.exceptions import ValidationError
from ..utils.result import Failure, Result, Success
from .dtos import CreatePlaylistRequest

T = TypeVar("T")


class IValidator(ABC, Generic[T]):
    """Base interface for validators."""

    @abstractmethod
    def validate(self, item: T) -> Result[T, List[ValidationError]]:
        """
        Validate an item.

        Args:
            item: Item to validate

        Returns:
            Success with item if valid, Failure with errors otherwise
        """
        pass


class PlaylistRequestValidator(IValidator[CreatePlaylistRequest]):
    """Validator for playlist creation requests."""

    MAX_NAME_LENGTH = 100
    MAX_TRACK_COUNT = 10000
    MIN_TRACK_COUNT = 1

    def validate(
        self, request: CreatePlaylistRequest
    ) -> Result[CreatePlaylistRequest, List[ValidationError]]:
        """Validate playlist request."""
        errors = []

        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            errors.append(ValidationError("Playlist name is required"))
        elif len(request.name) > self.MAX_NAME_LENGTH:
            errors.append(
                ValidationError(f"Playlist name too long (max {self.MAX_NAME_LENGTH} characters)")
            )

        # Validate update mode
        if request.update_mode not in ["replace", "append", "new"]:
            errors.append(ValidationError(f"Invalid update mode: {request.update_mode}"))

        # Validate tracks
        if len(request.track_ids) < self.MIN_TRACK_COUNT:
            errors.append(ValidationError(f"At least {self.MIN_TRACK_COUNT} track is required"))
        elif len(request.track_ids) > self.MAX_TRACK_COUNT:
            errors.append(ValidationError(f"Too many tracks (max {self.MAX_TRACK_COUNT})"))

        # Validate track IDs
        for track_id in request.track_ids:
            if not track_id or len(track_id.strip()) == 0:
                errors.append(ValidationError("Track IDs cannot be empty"))
                break

        return Failure(errors) if errors else Success(request)


class CompositeValidator(IValidator[T]):
    """Validator that combines multiple validators."""

    def __init__(self, *validators: IValidator[T]):
        """
        Initialize composite validator.

        Args:
            validators: Validators to combine
        """
        self.validators = validators

    def validate(self, item: T) -> Result[T, List[ValidationError]]:
        """Validate using all validators."""
        all_errors = []

        for validator in self.validators:
            result = validator.validate(item)
            if result.is_failure():
                all_errors.extend(result.error)

        return Failure(all_errors) if all_errors else Success(item)
