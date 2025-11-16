# Spotichart

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
![Tests](https://img.shields.io/badge/tests-654%20passed-success)
![Coverage](https://img.shields.io/badge/coverage-95.52%25-brightgreen)
![Quality](https://img.shields.io/badge/quality-ELITE%20Package-gold)
![GitHub](https://img.shields.io/badge/Install-From%20GitHub-blue?logo=github)

</div>

A professional, enterprise-grade Python application that automatically creates Spotify playlists based on top charts from Kworb.net.

[Features](#features) •
[Installation](#installation) •
[Usage](#usage) •
[Docker](#docker) •
[Documentation](#documentation) •
[Contributing](#contributing)

---

## Features

### Core Features
- **Automated Chart Scraping**: Extracts top songs from Kworb.net charts with retry logic
- **Multi-Region Support**: Brazil, Global, US, UK charts
- **Robust CLI**: Beautiful command-line interface powered by Click and Rich
- **Spotify Integration**: Seamless playlist creation with batch processing
- **Docker Support**: Fully containerized with multi-stage builds

### ELITE Package - Enterprise++ Quality 🚀
- **Property-Based Testing**: Automated edge case discovery with Hypothesis (14 tests)
- **Performance Benchmarks**: Track critical path performance with pytest-benchmark (14 benchmarks)
- **Security Scanning**: Zero vulnerabilities with Bandit & Safety
- **Type Safety**: Mypy strict mode for maximum type safety
- **Runtime Validation**: Pydantic V2 for DTOs with automatic validation
- **Quality Gates**: 8 pre-commit hooks ensuring code quality

### Architecture Excellence
- **SOLID Principles**: 100% compliance (SRP, OCP, LSP, ISP, DIP)
- **CQRS Pattern**: Complete Command/Query separation
- **Clean Architecture**: Domain-driven design with clear boundaries
- **Production Ready**: 654 tests, 95.52% coverage, comprehensive logging
- **Type-Safe**: Full type hints with strict mypy validation
- **CI/CD**: Automated testing, linting, and deployment

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Spotify Developer Account ([Create one here](https://developer.spotify.com/dashboard))
- Docker (optional, for containerized deployment)

### Installation

#### Option 1: Install from GitHub (Recommended)

Install directly from the GitHub repository:

```bash
# Install the latest version
pip install git+https://github.com/yurivalicelle/spotichart.git

# Or install a specific version/tag
pip install git+https://github.com/yurivalicelle/spotichart.git@v2.0.0

# Or install a specific branch
pip install git+https://github.com/yurivalicelle/spotichart.git@main
```

#### Option 2: Development Install (For Contributors)

```bash
# Clone the repository
git clone https://github.com/yurivalicelle/spotichart.git
cd spotichart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

#### Option 3: Docker

```bash
# Build the image
docker-compose build

# Run the application
docker-compose run spotichart config
```

### Configuration

1. **Create `.env` file from template:**

```bash
cp .env.example .env
```

2. **Add your Spotify credentials** to `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
REDIRECT_URI=http://localhost:8888/callback
```

3. **Verify configuration:**

```bash
spotichart config
```

## Usage

### Command-Line Interface

The CLI provides several commands for managing playlists:

#### Create a Playlist

```bash
# Create playlist from Brazil charts (default)
spotichart create

# Create from global charts with custom name
spotichart create --region global --name "Top Global 500" --limit 500

# Make playlist public
spotichart create --region us --public

# Enable debug logging
spotichart --debug create --region uk
```

#### Preview Charts

```bash
# Preview top 10 tracks from Brazil
spotichart preview --region brazil --limit 10

# Preview top 20 from global charts
spotichart preview --region global --limit 20
```

#### List Available Regions

```bash
spotichart regions
```

#### Check Configuration

```bash
spotichart config
```

### Python API

You can also use the package programmatically with the new SOLID architecture:

```python
from spotichart.core.factory import SpotifyServiceFactory
from spotichart.core.scraper import KworbScraper
from spotichart.config import Config

# Using the Factory Pattern with Dependency Injection
service = SpotifyServiceFactory.create()

# Or get the DependencyContainer for advanced usage
container = SpotifyServiceFactory.get_container()
playlist_manager = container.get_playlist_manager()
track_manager = container.get_track_manager()

# Scrape tracks
scraper = KworbScraper()
tracks = scraper.scrape_region('brazil', limit=100)

# Create playlist using the service
track_ids = [t['track'] for t in tracks]
track_uris = [track_manager.build_uri(tid) for tid in track_ids]

# Create playlist
playlist = playlist_manager.create(
    name="My Playlist",
    description="Top 100 from Brazil",
    public=False
)

# Add tracks
count = track_manager.add_to_playlist(playlist['id'], track_uris)

print(f"Created playlist: {playlist['external_urls']['spotify']}")
print(f"Added {count} tracks")
```

**Advanced: Custom Configuration**

```python
from pathlib import Path
from spotichart.utils.configuration_provider import ConfigurationProvider
from spotichart.core.factory import SpotifyServiceFactory

# Load custom configuration
config = ConfigurationProvider(config_file=Path('my_config.yaml'))

# Create service with custom config
service = SpotifyServiceFactory.create(config=config)
```

## Docker

### Using Docker Compose

```bash
# Build and run
docker-compose up

# Create a playlist
docker-compose run spotichart create --region brazil

# Preview charts
docker-compose run spotichart preview --region global --limit 20

# Run with custom environment
docker-compose run -e LOG_LEVEL=DEBUG spotichart create
```

### Using Docker Directly

```bash
# Build image
docker build -t spotichart .

# Run container
docker run --rm \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  spotichart create --region brazil
```

## Project Structure

```
spotichart/
├── .github/
│   └── workflows/          # CI/CD workflows
│       ├── ci.yml         # Testing and linting
│       └── docker.yml     # Docker build and push
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md    # Architecture overview
│   ├── COMMANDS_CHEATSHEET.md # CLI commands
│   ├── FINAL_REPORT.md    # Project final report
│   ├── SOLID_GUIDE.md     # SOLID principles guide
│   └── TROUBLESHOOTING.md # Troubleshooting guide
├── src/
│   └── spotichart/
│       ├── __init__.py
│       ├── config.py      # Configuration management
│       ├── cli/           # Command-line interface
│       │   ├── __init__.py
│       │   └── main.py
│       ├── core/          # Core business logic
│       │   ├── __init__.py
│       │   ├── spotify_client.py
│       │   └── scraper.py
│       └── utils/         # Utilities
│           ├── __init__.py
│           ├── exceptions.py
│           └── logger.py
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_spotify_client.py
│   ├── test_scraper.py
│   └── test_cli.py
├── templates/             # HTML templates (if using web interface)
├── .env.example          # Environment variables template
├── .gitignore
├── .dockerignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml        # Project configuration
├── Makefile
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Development

### Setting Up Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/github_username/spotichart.git
cd spotichart
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests (654 tests)
pytest

# Run with coverage (95.52% coverage)
pytest --cov=spotichart --cov-report=html

# Run specific test file
pytest tests/test_spotify_client.py -v

# Run property-based tests (Hypothesis)
pytest tests/test_property_based.py -v

# Run performance benchmarks
pytest tests/test_benchmarks.py --benchmark-only

# Run security scans
bandit -r src/spotichart
safety scan
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint code
flake8 src/
pylint src/

# Type checking
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Using Makefile

```bash
make install      # Install dependencies
make install-dev  # Install dev dependencies
make test         # Run tests
make lint         # Run linting
make format       # Format code
make clean        # Clean up cache files
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | Spotify app client ID | Required |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret | Required |
| `REDIRECT_URI` | OAuth callback URL | `http://localhost:8888/callback` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `PLAYLIST_LIMIT` | Default number of tracks | `1000` |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | `30` |
| `CACHE_ENABLED` | Enable caching | `True` |

### Supported Regions

- `brazil` - Brazil weekly charts
- `global` - Global weekly charts
- `us` - United States weekly charts
- `uk` - United Kingdom weekly charts

## Troubleshooting

If you encounter authentication problems:

1. Verify credentials in `.env` file
2. Check redirect URI matches Spotify app settings
3. Delete `.cache` directory and try again
4. Ensure you're using the latest version of Spotipy

If scraping fails:

1. Check internet connection
2. Verify Kworb.net is accessible
3. Review logs in `logs/spotichart.log`
4. Try again with `--debug` flag

### Docker Issues

```bash
# Clean up Docker resources
docker-compose down -v
docker system prune -a

# Rebuild image
docker-compose build --no-cache
```

## API Rate Limits

- **Kworb.net**: No official limits, but be respectful (built-in retry logic)
- **Spotify API**:
  - Maximum 100 tracks per batch (handled automatically)
  - Rate limits enforced per endpoint
  - Authentication tokens expire after 1 hour

## Documentation

For detailed information about the ELITE Package and architecture:

- **[ELITE_PACKAGE.md](ELITE_PACKAGE.md)** - Complete ELITE Package documentation
  - Property-Based Testing guide
  - Performance Benchmarking
  - Security Scanning setup
  - Type Safety with Mypy
  - Quality Gates and Pre-commit Hooks

- **[docs/ARCHITECTURE_IMPROVEMENTS.md](docs/ARCHITECTURE_IMPROVEMENTS.md)** - Future architecture improvements and proposals

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Security

- Never commit `.env` file
- Keep Spotify credentials private
- Use environment variables for sensitive data
- Docker images run as non-root user
- Pre-commit hooks check for private keys
- Security scanning with Bandit and Safety
- **Zero code vulnerabilities** (verified with Bandit)
- Dependency vulnerability scanning with Safety

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Kworb.net](https://kworb.net) for providing music chart data
- [Spotipy](https://spotipy.readthedocs.io/) for the Spotify Web API wrapper
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal formatting

## Changelog

### Version 2.0.0 - ELITE Package (Current)

**🚀 ELITE Package - Enterprise++ Quality:**
- Property-Based Testing with Hypothesis (14 tests, 1000s of generated cases)
- Performance Benchmarks with pytest-benchmark (14 benchmarks)
- Security Scanning: Bandit (0 issues), Safety (dependency checks)
- Mypy Strict Mode (maximum type safety)
- Pydantic V2 DTOs (runtime validation)
- 8 Pre-commit Hooks (quality gates)
- Mutation Testing configured

**📊 Metrics:**
- 654 tests (100% passing, +29 from previous version)
- 95.52% code coverage (exceeds 90% target)
- 0 security vulnerabilities in code
- SOLID 100% compliance

**🏗️ Architecture Excellence:**
- SOLID Principles (SRP, OCP, LSP, ISP, DIP)
- CQRS Pattern (Command/Query Separation)
- Result Monad for functional error handling
- Repository Pattern with caching
- Factory Pattern for dependency injection
- Strategy Pattern for update modes

**Major Refactoring:**
- Reorganized project with src layout
- Professional CLI with Click and Rich
- Docker support with multi-stage builds
- Comprehensive CI/CD with GitHub Actions
- Migrated to pyproject.toml (PEP 518)
- Enhanced error handling and custom exceptions
- Improved logging with rotation
- Full type hints with strict validation
- Extensive documentation

**Features:**
- Multi-region support (Brazil, Global, US, UK)
- Batch processing for Spotify API
- Retry logic for network requests
- Context managers for resource management
- Rich CLI with progress bars

### Version 1.0.0

- Initial release with basic functionality

## Support

- **Issues**: [GitHub Issues](https://github.com/github_username/spotichart/issues)
- **Discussions**: [GitHub Discussions](https://github.com/github_username/spotichart/discussions)
- **Documentation**: [Full Documentation](https://github.com/github_username/spotichart/wiki)

---

<div align="center">

Made with ❤️ by the community

[⬆ back to top](#spotichart)

</div>
