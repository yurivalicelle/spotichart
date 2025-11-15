"""
Custom Exceptions Module

Defines custom exception classes for better error handling.
"""


class SpotichartError(Exception):
    """Base exception for Spotichart."""

    pass


class SpotifyAuthError(SpotichartError):
    """Raised when Spotify authentication fails."""

    pass


class PlaylistCreationError(SpotichartError):
    """Raised when playlist creation or modification fails."""

    pass


class ScrapingError(SpotichartError):
    """Raised when web scraping fails."""

    pass


class ConfigurationError(SpotichartError):
    """Raised when configuration is invalid."""

    pass


class ValidationError(SpotichartError):
    """Raised when input validation fails."""

    pass


class TrackAdditionError(SpotichartError):
    """Raised when adding tracks to a playlist fails."""

    pass
