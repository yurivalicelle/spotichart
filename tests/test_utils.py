"""Tests for utility modules."""

import pytest
from pathlib import Path
from spotichart.utils.config_validator import ConfigValidator
from spotichart.utils.directory_manager import DirectoryManager


class TestConfigValidator:
    """Test ConfigValidator utility."""

    def test_validate_spotify_credentials_valid(self):
        """Valid Spotify credentials pass validation."""
        valid, error = ConfigValidator.validate_spotify_credentials(
            'valid_client_id',
            'valid_client_secret'
        )

        assert valid is True
        assert error is None

    def test_validate_spotify_credentials_missing_id(self):
        """Missing client ID fails validation."""
        valid, error = ConfigValidator.validate_spotify_credentials('', 'secret')

        assert valid is False
        assert 'client_id' in error.lower()

    def test_validate_spotify_credentials_missing_secret(self):
        """Missing client secret fails validation."""
        valid, error = ConfigValidator.validate_spotify_credentials('id', '')

        assert valid is False
        assert 'client_secret' in error.lower()

    def test_validate_redirect_uri_valid(self):
        """Valid redirect URI passes."""
        valid, error = ConfigValidator.validate_redirect_uri('http://localhost:8888/callback')

        assert valid is True
        assert error is None

    def test_validate_redirect_uri_invalid(self):
        """Invalid redirect URI fails."""
        valid, error = ConfigValidator.validate_redirect_uri('')

        assert valid is False
        assert 'redirect_uri' in error.lower()

    def test_validate_all_valid_config(self, config_dict):
        """Valid config passes all validations."""
        is_valid, errors = ConfigValidator.validate_all(config_dict)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_all_missing_required(self):
        """Missing required fields fail validation."""
        invalid_config = {'SPOTIFY_CLIENT_ID': ''}

        is_valid, errors = ConfigValidator.validate_all(invalid_config)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_numeric_positive(self):
        """Positive numeric values pass."""
        valid, error = ConfigValidator.validate_numeric('timeout', 30, min_value=1)

        assert valid is True
        assert error is None

    def test_validate_numeric_negative(self):
        """Negative numeric values fail when min_value set."""
        valid, error = ConfigValidator.validate_numeric('timeout', -5, min_value=1)

        assert valid is False
        assert 'timeout' in error.lower()

    def test_validate_numeric_zero_allowed(self):
        """Zero is allowed when min_value is 0."""
        valid, error = ConfigValidator.validate_numeric('batch_size', 0, min_value=0)

        assert valid is True


class TestDirectoryManager:
    """Test DirectoryManager utility."""

    def test_ensure_directory_exists_creates_new(self, tmp_path):
        """Create new directory."""
        new_dir = tmp_path / 'new_directory'

        result = DirectoryManager.ensure_directory_exists(new_dir, create=True)

        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_already_exists(self, tmp_path):
        """Directory already exists."""
        existing_dir = tmp_path / 'existing'
        existing_dir.mkdir()

        result = DirectoryManager.ensure_directory_exists(existing_dir, create=True)

        assert result is True
        assert existing_dir.exists()

    def test_ensure_directory_exists_no_create(self, tmp_path):
        """Don't create if create=False."""
        nonexistent = tmp_path / 'nonexistent'

        result = DirectoryManager.ensure_directory_exists(nonexistent, create=False)

        assert result is False
        assert not nonexistent.exists()

    def test_ensure_directory_exists_parent_missing(self, tmp_path):
        """Create parent directories."""
        nested_dir = tmp_path / 'parent' / 'child' / 'grandchild'

        result = DirectoryManager.ensure_directory_exists(nested_dir, create=True)

        assert result is True
        assert nested_dir.exists()
        assert nested_dir.parent.exists()

    def test_setup_app_directories(self, tmp_path, monkeypatch):
        """Setup application directories."""
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)

        dirs = DirectoryManager.setup_app_directories('test_app')

        assert 'base' in dirs
        assert 'cache' in dirs
        assert 'logs' in dirs
        assert dirs['base'].exists()
        assert dirs['cache'].exists()
        assert dirs['logs'].exists()

    def test_clean_directory_removes_files(self, tmp_path):
        """Clean directory removes files."""
        test_dir = tmp_path / 'to_clean'
        test_dir.mkdir()

        # Create test files
        (test_dir / 'file1.txt').write_text('content')
        (test_dir / 'file2.txt').write_text('content')

        DirectoryManager.clean_directory(test_dir, keep_structure=True)

        # Directory should exist but be empty
        assert test_dir.exists()
        assert len(list(test_dir.iterdir())) == 0

    def test_clean_directory_removes_structure(self, tmp_path):
        """Clean directory can remove structure."""
        test_dir = tmp_path / 'to_remove'
        test_dir.mkdir()
        (test_dir / 'file.txt').write_text('content')

        DirectoryManager.clean_directory(test_dir, keep_structure=False)

        assert not test_dir.exists()

    def test_is_writable_true(self, tmp_path):
        """Writable directory returns True."""
        result = DirectoryManager.is_writable(tmp_path)

        assert result is True

    def test_get_directory_size(self, tmp_path):
        """Get directory size."""
        test_dir = tmp_path / 'size_test'
        test_dir.mkdir()

        # Create files
        (test_dir / 'file1.txt').write_text('a' * 100)
        (test_dir / 'file2.txt').write_text('b' * 200)

        size = DirectoryManager.get_directory_size(test_dir)

        assert size >= 300  # At least 300 bytes
