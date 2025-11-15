# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Web dashboard interface
- Scheduled playlist updates
- Multi-user support with database
- Analytics and statistics
- ML-based recommendations
- Export to CSV/JSON

## [2.0.0] - 2025-01-13

### 🎉 Major Release - Complete Professional Refactoring

### Added

#### Architecture & Structure
- **src/ layout**: Modern Python package structure with proper module organization
- **Modular design**: Separated concerns into core, cli, and utils modules
- **Type safety**: Comprehensive type hints throughout the entire codebase
- **Custom exceptions**: Proper exception hierarchy for better error handling

#### CLI & User Experience
- **Click-based CLI**: Professional command-line interface with subcommands
- **Rich formatting**: Beautiful terminal output with progress bars and tables
- **Multiple commands**: create, preview, regions, config
- **Region support**: Brazil, Global, US, UK charts
- **Debug mode**: Enhanced logging with `--debug` flag

#### Development & Quality
- **pyproject.toml**: Modern Python packaging (PEP 518)
- **Pre-commit hooks**: Automated code quality checks
- **GitHub Actions**: CI/CD pipelines for testing and Docker builds
- **Docker support**: Multi-stage builds with security best practices
- **Comprehensive tests**: Unit tests with pytest and coverage reporting
- **Code formatters**: Black, isort for consistent code style
- **Linters**: Flake8, pylint, mypy for code quality
- **Security scanning**: Bandit and Trivy for vulnerability detection

#### Documentation
- **Architecture docs**: Detailed system architecture documentation
- **API documentation**: Complete API reference
- **Contributing guide**: Comprehensive contribution guidelines
- **Quick start guide**: 5-minute setup guide
- **README badges**: Status badges for CI, coverage, version, etc.
- **Changelog**: Semantic versioning changelog

#### Features
- **Retry logic**: Automatic retry with exponential backoff for network requests
- **Batch processing**: Efficient Spotify API usage with batching
- **Logging rotation**: Rotating log files with size limits
- **Config validation**: Startup validation of required configuration
- **Context managers**: Proper resource management
- **OAuth caching**: Token caching for better UX

### Changed

#### Breaking Changes
- **Package structure**: Moved from flat structure to src/ layout
- **Import paths**: Changed from `import app` to `from spotify_playlist_creator import ...`
- **CLI interface**: Changed from script to installable command `spotify-playlist`
- **Configuration**: Environment variables now centralized in Config class

#### Improvements
- **Error handling**: Better error messages with context and suggestions
- **Logging**: Structured logging with multiple levels and handlers
- **Performance**: Optimized with connection pooling and lazy loading
- **Security**: Credentials via environment variables, no hardcoded secrets
- **Maintainability**: Separated business logic from presentation layer

### Deprecated
- **Old app.py**: Legacy flat structure (kept for reference)
- **setup.py**: Replaced by pyproject.toml (but kept for compatibility)

### Removed
- **Hardcoded credentials**: Removed from all code
- **Direct file execution**: Use CLI command instead

### Fixed
- **Rate limiting**: Proper handling of Spotify API rate limits
- **Error propagation**: Exceptions now properly propagated with context
- **Resource leaks**: Proper cleanup with context managers
- **Type inconsistencies**: Fixed with comprehensive type hints

### Security
- **Credential management**: Environment variables only
- **Docker security**: Non-root user, minimal base image
- **Dependency scanning**: Automated security scans in CI
- **Secret detection**: Pre-commit hooks prevent credential commits

## [1.0.0] - 2024-02-01

### Initial Release

#### Added
- Basic Kworb scraping functionality
- Spotify playlist creation
- Brazil and Global chart support
- Simple HTML template interface
- Flask web server
- Basic error handling
- Simple logging

#### Features
- Create playlists from Kworb charts
- OAuth authentication with Spotify
- HTML web interface
- Basic configuration via .env

---

## Migration Guide

### From 1.x to 2.x

#### 1. Update Installation

**Old (1.x)**:
```bash
python app.py
```

**New (2.x)**:
```bash
pip install -e .
spotify-playlist create --region brazil
```

#### 2. Update Imports

**Old (1.x)**:
```python
import app
from kworb_parser import get_top_tracks
```

**New (2.x)**:
```python
from spotify_playlist_creator import SpotifyClient, KworbScraper
from spotify_playlist_creator.config import Config
```

#### 3. Update Configuration

**Old (1.x)**:
- Credentials hardcoded or in app.py

**New (2.x)**:
- All configuration in .env file
- Validation on startup
- Type-safe Config class

#### 4. Update Docker Usage

**Old (1.x)**:
```bash
docker run app python app.py
```

**New (2.x)**:
```bash
docker-compose run spotify-playlist create --region brazil
```

---

## Links

- [Source Code](https://github.com/yourusername/spotify-playlist-creator)
- [Issue Tracker](https://github.com/yourusername/spotify-playlist-creator/issues)
- [Documentation](https://github.com/yourusername/spotify-playlist-creator/wiki)
- [Releases](https://github.com/yourusername/spotify-playlist-creator/releases)
