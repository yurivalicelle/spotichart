# Spotichart

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Code Style](https://img.shields.io/badge/code%20style-black-black)
![CI](https://img.shields.io/github/actions/workflow/status/github_username/spotichart/ci.yml?branch=main&label=CI)
![Docker](https://img.shields.io/github/actions/workflow/status/github_username/spotichart/docker.yml?branch=main&label=Docker)
![Coverage](https://img.shields.io/codecov/c/github/github_username/spotichart)

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

- **Automated Chart Scraping**: Extracts top songs from Kworb.net charts with retry logic
- **Multi-Region Support**: Brazil, Global, US, UK charts
- **Robust CLI**: Beautiful command-line interface powered by Click and Rich
- **Spotify Integration**: Seamless playlist creation with batch processing
- **Docker Support**: Fully containerized with multi-stage builds
- **Production Ready**: Comprehensive logging, error handling, and monitoring
- **Type-Safe**: Full type hints throughout the codebase
- **Well-Tested**: Unit tests with pytest and coverage reports
- **CI/CD**: GitHub Actions workflows for testing and deployment
- **Code Quality**: Pre-commit hooks, linting, and formatting

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Spotify Developer Account ([Create one here](https://developer.spotify.com/dashboard))
- Docker (optional, for containerized deployment)

### Installation

#### Option 1: pip install (recommended)

```bash
# Clone the repository
git clone https://github.com/github_username/spotichart.git
cd spotichart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

#### Option 2: Docker

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

You can also use the package programmatically:

```python
from spotichart import SpotifyClient, KworbScraper, Config

# Initialize components
scraper = KworbScraper()
client = SpotifyClient()

# Scrape tracks
tracks = scraper.scrape_region('brazil', limit=100)

# Create playlist
url, count, failed = client.create_playlist_with_tracks(
    name="My Playlist",
    track_ids=[t['track'] for t in tracks],
    description="Top 100 from Brazil",
    public=False
)

print(f"Created playlist: {url}")
print(f"Added {count} tracks, {len(failed)} failed")
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
# Run all tests
pytest

# Run with coverage
pytest --cov=spotichart --cov-report=html

# Run specific test file
pytest tests/test_spotify_client.py -v
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

## Security

- Never commit `.env` file
- Keep Spotify credentials private
- Use environment variables for sensitive data
- Docker images run as non-root user
- Pre-commit hooks check for private keys
- Security scanning with Bandit and Trivy

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

### Version 2.0.0 (Current)

**Major Refactoring:**
- Reorganized project with src layout
- Added professional CLI with Click and Rich
- Implemented Docker support with multi-stage builds
- Added comprehensive CI/CD with GitHub Actions
- Migrated to pyproject.toml (PEP 518)
- Added pre-commit hooks
- Enhanced error handling and custom exceptions
- Improved logging with rotation
- Added type hints throughout
- Created extensive documentation
- Implemented code quality tools

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
