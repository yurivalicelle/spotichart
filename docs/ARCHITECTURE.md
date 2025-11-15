# Architecture Documentation

## Overview

Spotify Playlist Creator is built following clean architecture principles, with clear separation of concerns and a modular design.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer                            │
│  ┌────────────────────────────────────────────────┐    │
│  │   Click Commands (create, preview, regions)     │    │
│  │   Rich Console Output & Progress Bars           │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│               Core Business Logic                        │
│  ┌──────────────────┐      ┌────────────────────┐      │
│  │ SpotifyClient    │      │  KworbScraper      │      │
│  │ - OAuth          │      │  - HTTP Requests   │      │
│  │ - Playlist CRUD  │      │  - HTML Parsing    │      │
│  │ - Track Search   │      │  - Retry Logic     │      │
│  └──────────────────┘      └────────────────────┘      │
└──────────────────┬──────────────────┬───────────────────┘
                   │                  │
┌──────────────────▼──────────────────▼───────────────────┐
│                  Utilities Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Logger    │  │  Exceptions  │  │    Config    │   │
│  │   (Rotating)│  │  (Custom)    │  │  (Env Vars)  │   │
│  └─────────────┘  └──────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────┘
                   │                  │
┌──────────────────▼──────────────────▼───────────────────┐
│                External Services                         │
│  ┌─────────────────┐        ┌──────────────────┐       │
│  │ Spotify Web API │        │   Kworb.net      │       │
│  │ (via Spotipy)   │        │   (Web Scraping) │       │
│  └─────────────────┘        └──────────────────┘       │
└──────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Separation of Concerns

- **CLI Layer**: User interaction and presentation
- **Core Layer**: Business logic and domain models
- **Utils Layer**: Cross-cutting concerns (logging, config, errors)
- **External Services**: Third-party integrations

### 2. Dependency Injection

- Configuration injected via environment variables
- Dependencies passed explicitly to constructors
- Easy to mock for testing

### 3. Error Handling

- Custom exception hierarchy
- Proper error propagation
- User-friendly error messages
- Detailed logging for debugging

### 4. Configuration Management

- Centralized in `Config` class
- Environment variable based
- Validation on startup
- Default values provided

## Module Structure

### CLI Module (`cli/`)

**Purpose**: Command-line interface implementation

**Components**:
- `main.py`: Click command definitions with Rich formatting

**Responsibilities**:
- Parse command-line arguments
- Display formatted output
- Handle user interaction
- Orchestrate core components

### Core Module (`core/`)

**Purpose**: Core business logic

**Components**:

#### `spotify_client.py`
- Handles Spotify API authentication
- Manages playlist creation and modification
- Searches for tracks
- Implements batch processing
- Handles rate limiting

Key Methods:
- `authenticate()`: OAuth flow
- `create_playlist()`: Create new playlist
- `add_tracks_to_playlist()`: Add tracks in batches
- `create_playlist_with_tracks()`: End-to-end workflow

#### `scraper.py`
- Scrapes Kworb.net charts
- Parses HTML tables
- Implements retry logic
- Handles network errors

Key Methods:
- `scrape()`: Main scraping logic
- `scrape_region()`: Region-specific scraping
- `_fetch_page()`: HTTP request with retries
- `_parse_table()`: HTML parsing

### Utils Module (`utils/`)

**Purpose**: Shared utilities and infrastructure

**Components**:

#### `exceptions.py`
Custom exception hierarchy:
```python
SpotifyPlaylistError (base)
├── SpotifyAuthError
├── PlaylistCreationError
├── ScrapingError
├── ConfigurationError
└── ValidationError
```

#### `logger.py`
- Rotating file handler
- Console output
- Structured formatting
- Multiple log levels

#### `config.py`
- Environment variable loading
- Configuration validation
- Default values
- Path management

## Data Flow

### Creating a Playlist

```
1. User Command
   spotify-playlist create --region brazil --limit 500
          │
          ▼
2. CLI Layer (main.py)
   - Parse arguments
   - Validate input
   - Initialize progress bar
          │
          ▼
3. Configuration Validation
   - Check credentials
   - Load environment variables
          │
          ▼
4. Scraper (scraper.py)
   - Fetch Kworb HTML
   - Parse table
   - Extract track IDs
   - Retry on failure
          │
          ▼
5. Spotify Client (spotify_client.py)
   - Authenticate via OAuth
   - Create empty playlist
   - Search for each track
   - Batch add tracks (100 at a time)
          │
          ▼
6. Result Display
   - Show playlist URL
   - Report statistics
   - Log failures
```

## Error Handling Strategy

### 1. Network Errors

```python
# Automatic retry with exponential backoff
for attempt in range(max_retries):
    try:
        response = session.get(url)
        response.raise_for_status()
        break
    except RequestException:
        time.sleep(retry_delay * attempt)
```

### 2. Authentication Errors

```python
# Clear error messages and user guidance
if not Config.validate():
    console.print("[red]Missing credentials!")
    console.print("Set SPOTIFY_CLIENT_ID in .env")
    sys.exit(1)
```

### 3. API Rate Limits

```python
# Batch processing with delays
for i in range(0, len(tracks), batch_size):
    batch = tracks[i:i + batch_size]
    sp.playlist_add_items(playlist_id, batch)
    time.sleep(0.5)  # Avoid rate limits
```

## Logging Architecture

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (e.g., tracks not found)
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Log Rotation

- Maximum file size: 10MB
- Backup count: 5 files
- Automatic rotation
- Preserves historical logs

### Log Format

```
2024-01-15 14:30:22 - spotify_client - INFO - [spotify_client.py:45] - Creating playlist: Top 500
```

## Configuration Management

### Environment Variables

1. **Required**:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`

2. **Optional**:
   - `REDIRECT_URI` (default: http://localhost:8888/callback)
   - `LOG_LEVEL` (default: INFO)
   - `PLAYLIST_LIMIT` (default: 1000)
   - `REQUEST_TIMEOUT` (default: 30)

### Validation

```python
@classmethod
def validate(cls) -> bool:
    """Validate required configuration."""
    return bool(cls.SPOTIFY_CLIENT_ID and cls.SPOTIFY_CLIENT_SECRET)
```

## Testing Strategy

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Test error conditions
- Verify edge cases

### Integration Tests

- Test component interactions
- Use real API calls (with test data)
- Verify end-to-end workflows

### Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths
- All error handlers tested

## Performance Considerations

### 1. Batch Processing

- Add max 100 tracks per API call
- Reduces API calls significantly
- Handles Spotify rate limits

### 2. Connection Pooling

```python
self.session = requests.Session()
# Reuses HTTP connections
```

### 3. Lazy Loading

```python
@property
def sp(self) -> spotipy.Spotify:
    if self._sp is None:
        self._authenticate()
    return self._sp
```

### 4. Caching

- Spotify auth tokens cached
- Reduces authentication overhead

## Security Considerations

### 1. Credentials Management

- Never hardcode credentials
- Use environment variables
- Excluded from version control
- Docker secrets support

### 2. Input Validation

- Validate region names
- Sanitize user input
- Limit playlist sizes

### 3. Rate Limiting

- Respect API rate limits
- Implement backoff strategies
- Monitor API usage

### 4. Error Information

- Don't expose sensitive data in logs
- Sanitize error messages
- Secure logging practices

## Scalability

### Current Limitations

- Sequential track processing
- Single-threaded scraping
- No distributed processing

### Future Improvements

1. **Async Processing**
   ```python
   async def add_tracks():
       tasks = [add_track(tid) for tid in track_ids]
       await asyncio.gather(*tasks)
   ```

2. **Parallel Scraping**
   - Scrape multiple regions concurrently
   - Use thread pools

3. **Caching Layer**
   - Cache scraped data
   - Reduce API calls
   - Redis integration

4. **Database Integration**
   - Store playlist history
   - Track metrics
   - User preferences

## Deployment

### Docker

- Multi-stage builds for smaller images
- Non-root user for security
- Health checks implemented
- Volume mounts for logs

### CI/CD

- Automated testing on push
- Docker image building
- Security scanning
- Code quality checks

## Monitoring

### Metrics to Track

1. **Performance**:
   - Scraping time
   - API response times
   - Playlist creation time

2. **Reliability**:
   - Success/failure rates
   - Retry counts
   - Error frequencies

3. **Usage**:
   - Playlists created
   - Tracks processed
   - Regions accessed

### Logging Best Practices

```python
# Structured logging
logger.info(
    f"Playlist created: {count} tracks added, "
    f"{len(failed)} failed"
)

# Context information
logger.error(f"Failed to scrape {url}: {error}", exc_info=True)
```

## Maintenance

### Code Quality

- Pre-commit hooks enforce standards
- Black for consistent formatting
- Mypy for type checking
- Pylint for code quality

### Documentation

- Docstrings for all public APIs
- Type hints for clarity
- Architecture documentation
- API documentation

### Dependencies

- Regular updates via Dependabot
- Security scanning
- Version pinning in production
- Testing before upgrades

## Future Enhancements

1. **Web Interface**: Flask/FastAPI web app
2. **Scheduled Updates**: Cron jobs for playlist updates
3. **Multi-user Support**: Database for user data
4. **Analytics Dashboard**: Visualize playlist stats
5. **Recommendation Engine**: ML-based track suggestions
6. **Collaborative Playlists**: Multi-user editing
7. **Export Formats**: Support CSV, JSON exports
8. **Integration**: Third-party music service support
