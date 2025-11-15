"""
Result Pattern for Error Handling

Provides a functional approach to error handling without exceptions.
"""

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful result."""

    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """Transform the success value."""
        return Success(func(self.value))

    def flat_map(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Chain operations that return Results."""
        return func(self.value)

    def unwrap(self) -> T:
        """Extract the success value."""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Extract value or return default."""
        return self.value

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """Extract value or compute from error."""
        return self.value


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed result."""

    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """Transform does nothing on failure."""
        return self

    def flat_map(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Chain does nothing on failure."""
        return self

    def unwrap(self) -> T:
        """Raises the error."""
        raise self.error if isinstance(self.error, Exception) else Exception(str(self.error))

    def unwrap_or(self, default: T) -> T:
        """Return default on failure."""
        return default

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """Compute value from error."""
        return func(self.error)


# Type alias for Result
Result = Union[Success[T], Failure[E]]


def safe_execute(func: Callable[[], T], error_type: type = Exception) -> Result[T, Exception]:
    """
    Execute a function and wrap result in Success/Failure.

    Args:
        func: Function to execute
        error_type: Type of exception to catch

    Returns:
        Success with result or Failure with exception
    """
    try:
        return Success(func())
    except error_type as e:
        return Failure(e)
