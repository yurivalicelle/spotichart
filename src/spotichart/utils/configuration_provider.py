"""
Configuration Provider Module

Provides configuration from YAML file following Dependency Inversion Principle.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None
from dotenv import load_dotenv
from .interfaces import IConfiguration
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigurationProvider(IConfiguration):
    """
    Configuration provider that loads from YAML file and environment variables.
    Implements IConfiguration interface.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration provider.

        Args:
            config_file: Path to YAML configuration file.
                        If None, searches for config.yaml in project root.

        Raises:
            ConfigurationError: If configuration file is not found or invalid
        """
        self._config: Dict[str, Any] = {}
        self._env_loaded = False

        # Load environment variables
        self._load_env()

        # Determine config file path
        if config_file is None:
            # Search for config.yaml in project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_file = project_root / "config.yaml"

        self.config_file = config_file

        # Load YAML configuration
        self._load_yaml_config()

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if not self._env_loaded:
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                logger.info(f"Loaded environment variables from {env_path}")
            self._env_loaded = True

    def _load_yaml_config(self) -> None:
        """
        Load configuration from YAML file.

        Raises:
            ConfigurationError: If file is not found or invalid
        """
        if yaml is None:
            logger.warning("PyYAML not installed, using default configuration")
            self._config = self._get_default_config()
            return

        if not self.config_file.exists():
            logger.warning(f"Configuration file not found: {self.config_file}")
            logger.warning("Using default configuration and environment variables only")
            self._config = self._get_default_config()
            return

        try:
            with open(self.config_file, "r") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_file}")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {str(e)}")
            raise ConfigurationError(f"Invalid YAML configuration: {str(e)}") from e

        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration when YAML file is not available.

        Returns:
            Default configuration dictionary
        """
        return {
            "app": {"name": "Spotichart", "version": "2.0.0"},
            "spotify": {
                "scope": "playlist-modify-private playlist-modify-public",
                "batch_size": 100,
                "max_retries": 3,
                "retry_delay": 2,
            },
            "kworb_urls": {
                "brazil": {
                    "url": "https://kworb.net/spotify/country/br_weekly_totals.html",
                    "display_name": "Brazil",
                },
                "global": {
                    "url": "https://kworb.net/spotify/country/global_weekly_totals.html",
                    "display_name": "Global",
                },
            },
            "settings": {"default_playlist_limit": 1000, "request_timeout": 30},
            "cache": {"enabled": True, "ttl_hours": 24},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "max_bytes": 10485760,
                "backup_count": 5,
                "log_file": "logs/spotichart.log",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., 'spotify.client_id', 'settings.request_timeout')
            default: Default value if key is not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get('spotify.scope')
            'playlist-modify-private playlist-modify-public'
            >>> config.get('settings.request_timeout')
            30
        """
        # Try environment variable first for sensitive data
        env_key = key.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Navigate through nested dictionary
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_kworb_url(self, region: str = "brazil") -> str:
        """
        Get Kworb URL for specific region.

        Args:
            region: Region identifier

        Returns:
            URL for the specified region
        """
        kworb_urls = self.get("kworb_urls", {})

        # Ensure kworb_urls is a dict
        if not isinstance(kworb_urls, dict):
            return ""

        region_config = kworb_urls.get(region.lower())

        if region_config and isinstance(region_config, dict):
            return region_config.get("url", "")

        # Fallback to brazil
        brazil_config = kworb_urls.get("brazil", {})
        return brazil_config.get("url", "") if isinstance(brazil_config, dict) else ""

    def get_available_regions(self) -> List[str]:
        """
        Get list of available regions.

        Returns:
            List of region names
        """
        kworb_urls = self.get("kworb_urls", {})
        return list(kworb_urls.keys())

    def validate(self) -> bool:
        """
        Validate that required configuration values are present.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_env_vars = ["SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"]

        missing = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing.append(var)

        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            logger.error("Please set these variables in your .env file")
            return False

        # Validate essential configuration
        if not self.get("spotify.scope"):
            logger.error("Missing Spotify scope in configuration")
            return False

        logger.info("Configuration validation successful")
        return True

    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading configuration")
        self._load_yaml_config()
