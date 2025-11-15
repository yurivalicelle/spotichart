"""Tests for ConfigurationProvider."""

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from spotichart.utils.configuration_provider import ConfigurationProvider
from spotichart.utils.exceptions import ConfigurationError


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.yaml"
    config_content = """
app:
  name: "TestApp"
  version: "1.0.0"

spotify:
  scope: "test-scope"
  batch_size: 50

kworb_urls:
  brazil:
    url: "https://test.com/brazil"
    display_name: "Brazil"
  global:
    url: "https://test.com/global"
    display_name: "Global"

settings:
  default_playlist_limit: 500
  request_timeout: 20

cache:
  enabled: true
  ttl_hours: 12
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "SPOTIFY_CLIENT_ID": "test_client_id",
            "SPOTIFY_CLIENT_SECRET": "test_secret",
            "REDIRECT_URI": "http://test.com/callback",
        },
    ):
        yield


class TestConfigurationProviderInit:
    """Tests for ConfigurationProvider initialization."""

    def test_init_with_config_file(self, temp_config_file):
        """Should load configuration from YAML file."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.config_file == temp_config_file
        assert config.get("app.name") == "TestApp"
        assert config.get("app.version") == "1.0.0"

    def test_init_without_config_file_uses_default(self):
        """Should use default configuration if file doesn't exist."""
        non_existent = Path("/tmp/nonexistent_config.yaml")
        config = ConfigurationProvider(config_file=non_existent)

        # Should have default values
        assert config.get("app.name") == "Spotichart"
        assert config.get("spotify.batch_size") == 100

    @patch("spotichart.utils.configuration_provider.yaml", None)
    def test_init_without_yaml_library(self):
        """Should use defaults if PyYAML is not installed."""
        config = ConfigurationProvider()

        # Should have default values
        assert config.get("app.name") == "Spotichart"
        assert config.get("spotify.scope") is not None


class TestConfigurationProviderGet:
    """Tests for get method."""

    def test_get_simple_key(self, temp_config_file):
        """Should get value by simple key."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.get("spotify.batch_size") == 50

    def test_get_nested_key(self, temp_config_file):
        """Should get value by nested key."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.get("kworb_urls.brazil.url") == "https://test.com/brazil"

    def test_get_with_default(self, temp_config_file):
        """Should return default if key not found."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.get("non.existent.key", "default_value") == "default_value"

    def test_get_environment_variable_priority(self, temp_config_file, mock_env):
        """Should prioritize environment variables over config file."""
        config = ConfigurationProvider(config_file=temp_config_file)

        # Env var should override config file
        assert config.get("spotify_client_id") == "test_client_id"
        assert config.get("SPOTIFY_CLIENT_ID") == "test_client_id"

    def test_get_returns_none_for_missing_key(self, temp_config_file):
        """Should return None for missing key without default."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.get("missing.key") is None


class TestConfigurationProviderKworbUrls:
    """Tests for Kworb URL methods."""

    def test_get_kworb_url_existing_region(self, temp_config_file):
        """Should return URL for existing region."""
        config = ConfigurationProvider(config_file=temp_config_file)

        url = config.get_kworb_url("brazil")
        assert url == "https://test.com/brazil"

    def test_get_kworb_url_case_insensitive(self, temp_config_file):
        """Should handle region case-insensitively."""
        config = ConfigurationProvider(config_file=temp_config_file)

        url = config.get_kworb_url("BRAZIL")
        assert url == "https://test.com/brazil"

    def test_get_kworb_url_fallback_to_brazil(self, temp_config_file):
        """Should fallback to brazil for unknown region."""
        config = ConfigurationProvider(config_file=temp_config_file)

        url = config.get_kworb_url("unknown_region")
        assert url == "https://test.com/brazil"

    def test_get_available_regions(self, temp_config_file):
        """Should return list of available regions."""
        config = ConfigurationProvider(config_file=temp_config_file)

        regions = config.get_available_regions()
        assert "brazil" in regions
        assert "global" in regions


class TestConfigurationProviderValidation:
    """Tests for configuration validation."""

    def test_validate_success(self, temp_config_file, mock_env):
        """Should validate successfully with required env vars."""
        config = ConfigurationProvider(config_file=temp_config_file)

        assert config.validate() is True

    @patch("spotichart.utils.configuration_provider.load_dotenv")
    def test_validate_failure_missing_client_id(self, mock_load_dotenv, temp_config_file):
        """Should fail validation without SPOTIFY_CLIENT_ID."""
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigurationProvider(config_file=temp_config_file)

            assert config.validate() is False

    @patch("spotichart.utils.configuration_provider.load_dotenv")
    def test_validate_failure_missing_client_secret(self, mock_load_dotenv, temp_config_file):
        """Should fail validation without SPOTIFY_CLIENT_SECRET."""
        with patch.dict(os.environ, {"SPOTIFY_CLIENT_ID": "test"}, clear=True):
            config = ConfigurationProvider(config_file=temp_config_file)

            assert config.validate() is False

    def test_validate_failure_missing_scope(self):
        """Should fail validation without spotify scope in config."""
        config = ConfigurationProvider()
        config._config = {}  # Empty config

        with patch.dict(
            os.environ, {"SPOTIFY_CLIENT_ID": "test", "SPOTIFY_CLIENT_SECRET": "secret"}
        ):
            assert config.validate() is False


class TestConfigurationProviderReload:
    """Tests for reload functionality."""

    def test_reload_updates_config(self, temp_config_file):
        """Should reload configuration from file."""
        config = ConfigurationProvider(config_file=temp_config_file)

        original_value = config.get("app.name")
        assert original_value == "TestApp"

        # Modify file
        new_content = """
app:
  name: "UpdatedApp"
  version: "2.0.0"
"""
        temp_config_file.write_text(new_content)

        # Reload
        config.reload()

        assert config.get("app.name") == "UpdatedApp"


class TestConfigurationProviderErrorHandling:
    """Tests for error handling."""

    def test_invalid_yaml_raises_error(self, tmp_path):
        """Should raise ConfigurationError for invalid YAML."""
        bad_config = tmp_path / "bad_config.yaml"
        bad_config.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            ConfigurationProvider(config_file=bad_config)

    def test_file_read_error(self, tmp_path):
        """Should handle file read errors gracefully."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("app:\n  name: test")

        config = ConfigurationProvider(config_file=config_file)

        # Remove file to cause read error on reload
        config_file.unlink()

        # Should fall back to defaults
        config.reload()
        assert config.get("app.name") == "Spotichart"


class TestConfigurationProviderDefaults:
    """Tests for default configuration."""

    def test_default_config_structure(self):
        """Should have correct default config structure."""
        # Use non-existent file to trigger defaults
        config = ConfigurationProvider(config_file=Path("/tmp/nonexistent.yaml"))

        assert config.get("app.name") == "Spotichart"
        assert config.get("app.version") == "2.0.0"
        assert config.get("spotify.batch_size") == 100
        assert config.get("spotify.max_retries") == 3
        assert config.get("settings.default_playlist_limit") == 1000
        assert config.get("cache.enabled") is True

    def test_default_kworb_urls(self):
        """Should have default Kworb URLs."""
        config = ConfigurationProvider(config_file=Path("/tmp/nonexistent.yaml"))

        regions = config.get_available_regions()
        assert "brazil" in regions
        assert "global" in regions

        brazil_url = config.get_kworb_url("brazil")
        assert "kworb.net" in brazil_url


class TestConfigurationProviderEdgeCases:
    """Tests for edge cases."""

    def test_get_with_empty_key(self, temp_config_file):
        """Should handle empty key."""
        config = ConfigurationProvider(config_file=temp_config_file)

        result = config.get("", "default")
        assert result == "default"

    def test_get_from_none_value(self, temp_config_file):
        """Should handle None values in config."""
        config = ConfigurationProvider(config_file=temp_config_file)
        config._config["test"] = None

        result = config.get("test", "default")
        assert result is None  # None is a valid value

    def test_kworb_url_with_non_dict_config(self):
        """Should handle non-dict kworb_urls config."""
        config = ConfigurationProvider(config_file=Path("/tmp/nonexistent.yaml"))
        config._config["kworb_urls"] = "not_a_dict"

        # Should not crash, should return empty or fallback
        url = config.get_kworb_url("brazil")
        # Since kworb_urls is not a dict, it will fail to get region
        # and return empty string or fall back to brazil which is also not available
        assert url == "" or url is None

    def test_kworb_url_with_non_dict_region(self):
        """Should handle non-dict region config."""
        config = ConfigurationProvider(config_file=Path("/tmp/nonexistent.yaml"))
        config._config["kworb_urls"] = {"brazil": "not_a_dict"}

        # Should not crash
        url = config.get_kworb_url("brazil")
        assert url == ""
