"""
Tests for Validators
"""

import pytest

from spotichart.application.dtos import CreatePlaylistRequest
from spotichart.application.validators import CompositeValidator, IValidator, PlaylistRequestValidator
from spotichart.utils.exceptions import ValidationError
from spotichart.utils.result import Failure, Success


class TestPlaylistRequestValidator:
    """Test PlaylistRequestValidator."""

    def test_validate_valid_request(self):
        """Test validation of valid request."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test Playlist",
            track_ids=["track1", "track2"],
            description="Test description",
            public=True,
            update_mode="replace",
        )

        result = validator.validate(request)

        assert result.is_success()
        assert result.unwrap() == request

    def test_validate_empty_name(self):
        """Test validation fails for empty name."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="",
            track_ids=["track1"],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 1
        assert "name is required" in str(errors[0]).lower()

    def test_validate_whitespace_only_name(self):
        """Test validation fails for whitespace-only name."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="   ",
            track_ids=["track1"],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("name is required" in str(e).lower() for e in errors)

    def test_validate_name_too_long(self):
        """Test validation fails for name that's too long."""
        validator = PlaylistRequestValidator()
        long_name = "A" * (PlaylistRequestValidator.MAX_NAME_LENGTH + 1)
        request = CreatePlaylistRequest(
            name=long_name,
            track_ids=["track1"],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("name too long" in str(e).lower() for e in errors)

    def test_validate_invalid_update_mode(self):
        """Test validation fails for invalid update mode."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=["track1"],
            update_mode="invalid_mode",
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("invalid update mode" in str(e).lower() for e in errors)

    def test_validate_no_tracks(self):
        """Test validation fails when no tracks."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=[],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("track is required" in str(e).lower() for e in errors)

    def test_validate_too_many_tracks(self):
        """Test validation fails when too many tracks."""
        validator = PlaylistRequestValidator()
        too_many_tracks = ["track"] * (PlaylistRequestValidator.MAX_TRACK_COUNT + 1)
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=too_many_tracks,
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("too many tracks" in str(e).lower() for e in errors)

    def test_validate_empty_track_id(self):
        """Test validation fails when track ID is empty."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=["track1", "", "track3"],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("cannot be empty" in str(e).lower() for e in errors)

    def test_validate_whitespace_track_id(self):
        """Test validation fails when track ID is whitespace."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=["track1", "   ", "track3"],
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert any("cannot be empty" in str(e).lower() for e in errors)

    def test_validate_multiple_errors(self):
        """Test validation collects multiple errors."""
        validator = PlaylistRequestValidator()
        request = CreatePlaylistRequest(
            name="",  # Error 1: empty name
            track_ids=[],  # Error 2: no tracks
            update_mode="bad_mode",  # Error 3: invalid update mode
        )

        result = validator.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 3

    def test_validate_all_update_modes(self):
        """Test all valid update modes."""
        validator = PlaylistRequestValidator()

        for mode in ["replace", "append", "new"]:
            request = CreatePlaylistRequest(
                name="Test",
                track_ids=["track1"],
                update_mode=mode,
            )

            result = validator.validate(request)
            assert result.is_success(), f"Mode {mode} should be valid"


class DummyValidator(IValidator[CreatePlaylistRequest]):
    """Dummy validator for testing CompositeValidator."""

    def __init__(self, should_fail: bool = False, error_message: str = "Dummy error"):
        self.should_fail = should_fail
        self.error_message = error_message

    def validate(self, request: CreatePlaylistRequest):
        """Validate."""
        if self.should_fail:
            return Failure([ValidationError(self.error_message)])
        return Success(request)


class TestCompositeValidator:
    """Test CompositeValidator."""

    def test_validate_all_pass(self):
        """Test when all validators pass."""
        validator1 = DummyValidator(should_fail=False)
        validator2 = DummyValidator(should_fail=False)

        composite = CompositeValidator(validator1, validator2)
        request = CreatePlaylistRequest(name="Test", track_ids=["track1"])

        result = composite.validate(request)

        assert result.is_success()

    def test_validate_one_fails(self):
        """Test when one validator fails."""
        validator1 = DummyValidator(should_fail=False)
        validator2 = DummyValidator(should_fail=True, error_message="Error from validator 2")

        composite = CompositeValidator(validator1, validator2)
        request = CreatePlaylistRequest(name="Test", track_ids=["track1"])

        result = composite.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 1
        assert "Error from validator 2" in str(errors[0])

    def test_validate_multiple_failures(self):
        """Test when multiple validators fail."""
        validator1 = DummyValidator(should_fail=True, error_message="Error 1")
        validator2 = DummyValidator(should_fail=True, error_message="Error 2")
        validator3 = DummyValidator(should_fail=True, error_message="Error 3")

        composite = CompositeValidator(validator1, validator2, validator3)
        request = CreatePlaylistRequest(name="Test", track_ids=["track1"])

        result = composite.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 3
        assert "Error 1" in str(errors[0])
        assert "Error 2" in str(errors[1])
        assert "Error 3" in str(errors[2])

    def test_validate_mixed_results(self):
        """Test when some validators pass and some fail."""
        validator1 = DummyValidator(should_fail=False)
        validator2 = DummyValidator(should_fail=True, error_message="Error 2")
        validator3 = DummyValidator(should_fail=False)
        validator4 = DummyValidator(should_fail=True, error_message="Error 4")

        composite = CompositeValidator(validator1, validator2, validator3, validator4)
        request = CreatePlaylistRequest(name="Test", track_ids=["track1"])

        result = composite.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 2
        assert "Error 2" in str(errors[0])
        assert "Error 4" in str(errors[1])

    def test_validate_no_validators(self):
        """Test composite validator with no validators."""
        composite = CompositeValidator()
        request = CreatePlaylistRequest(name="Test", track_ids=["track1"])

        result = composite.validate(request)

        assert result.is_success()

    def test_composite_with_real_validator(self):
        """Test composite with real PlaylistRequestValidator."""
        real_validator = PlaylistRequestValidator()
        dummy_validator = DummyValidator(should_fail=True, error_message="Custom error")

        composite = CompositeValidator(real_validator, dummy_validator)

        # Valid request but dummy fails
        request = CreatePlaylistRequest(
            name="Test",
            track_ids=["track1"],
            update_mode="replace",
        )

        result = composite.validate(request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 1
        assert "Custom error" in str(errors[0])

        # Invalid request and dummy fails
        invalid_request = CreatePlaylistRequest(
            name="",  # Invalid
            track_ids=["track1"],
        )

        result = composite.validate(invalid_request)

        assert result.is_failure()
        errors = result.error
        assert len(errors) == 2  # One from real validator, one from dummy
