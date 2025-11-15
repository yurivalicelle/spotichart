"""
Tests for Result Pattern
"""

import pytest

from spotichart.utils.result import Failure, Result, Success, safe_execute


class TestSuccess:
    """Test Success result type."""

    def test_is_success(self):
        """Success should return True for is_success."""
        result = Success(42)
        assert result.is_success()
        assert not result.is_failure()

    def test_unwrap(self):
        """Success should unwrap to value."""
        result = Success(42)
        assert result.unwrap() == 42

    def test_unwrap_or(self):
        """Success should return value, not default."""
        result = Success(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_else(self):
        """Success should return value, not compute from error."""
        result = Success(42)
        assert result.unwrap_or_else(lambda e: 0) == 42

    def test_map(self):
        """Success should map value."""
        result = Success(42)
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_success()
        assert mapped.unwrap() == 84

    def test_flat_map(self):
        """Success should flat_map to new result."""
        result = Success(42)
        mapped = result.flat_map(lambda x: Success(x * 2))
        assert mapped.is_success()
        assert mapped.unwrap() == 84

    def test_flat_map_to_failure(self):
        """Success can flat_map to Failure."""
        result = Success(42)
        mapped = result.flat_map(lambda x: Failure("error"))
        assert mapped.is_failure()


class TestFailure:
    """Test Failure result type."""

    def test_is_failure(self):
        """Failure should return True for is_failure."""
        result = Failure("error")
        assert result.is_failure()
        assert not result.is_success()

    def test_unwrap_raises(self):
        """Failure should raise on unwrap."""
        result = Failure(ValueError("test error"))
        with pytest.raises(ValueError, match="test error"):
            result.unwrap()

    def test_unwrap_string_error(self):
        """Failure with string error should raise Exception."""
        result = Failure("string error")
        with pytest.raises(Exception, match="string error"):
            result.unwrap()

    def test_unwrap_or(self):
        """Failure should return default."""
        result = Failure("error")
        assert result.unwrap_or(42) == 42

    def test_unwrap_or_else(self):
        """Failure should compute from error."""
        result = Failure("error")
        assert result.unwrap_or_else(lambda e: f"Got: {e}") == "Got: error"

    def test_map(self):
        """Failure should not map."""
        result = Failure("error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.is_failure()
        assert mapped.error == "error"

    def test_flat_map(self):
        """Failure should not flat_map."""
        result = Failure("error")
        mapped = result.flat_map(lambda x: Success(x * 2))
        assert mapped.is_failure()
        assert mapped.error == "error"


class TestSafeExecute:
    """Test safe_execute helper."""

    def test_safe_execute_success(self):
        """safe_execute should wrap successful result."""
        result = safe_execute(lambda: 42)
        assert result.is_success()
        assert result.unwrap() == 42

    def test_safe_execute_failure(self):
        """safe_execute should catch exceptions."""

        def failing_func():
            raise ValueError("test error")

        result = safe_execute(failing_func)
        assert result.is_failure()
        assert isinstance(result.error, ValueError)

    def test_safe_execute_specific_error(self):
        """safe_execute should catch specific error types."""

        def failing_func():
            raise ValueError("test error")

        result = safe_execute(failing_func, error_type=ValueError)
        assert result.is_failure()

    def test_safe_execute_wrong_error_type(self):
        """safe_execute should not catch wrong error type."""

        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            safe_execute(failing_func, error_type=TypeError)
