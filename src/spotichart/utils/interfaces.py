"""
Utility Interfaces Module

Defines interfaces for utility components.
"""

from abc import ABC, abstractmethod
from typing import Any


class IConfiguration(ABC):
    """Interface for configuration providers."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate configuration."""
        pass
