# Contributing to Spotichart

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- Git

### Setting Up Your Development Environment

```bash
# Clone your fork
git clone https://github.com/yourusername/spotichart.git
cd spotichart

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Copy environment variables template
cp .env.example .env
# Edit .env with your Spotify credentials
```

## Code Style

This project follows these coding standards:

- **PEP 8**: Follow Python's style guide
- **Type Hints**: Add type hints to all function signatures
- **Docstrings**: Document all functions, classes, and modules using Google-style docstrings
- **Line Length**: Maximum 100 characters per line
- **SOLID Principles**: Follow SOLID design principles (see docs/SOLID_GUIDE.md)
- **Dependency Injection**: Use interfaces and dependency injection for loose coupling

### Example Function

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this error is raised
    """
    # Implementation here
    pass
```

## Testing

Before submitting a pull request, ensure that:

1. All tests pass
2. Code coverage is at least 90%
3. You've added tests for new functionality
4. Edge cases are covered
5. No existing functionality is broken

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=spotichart --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_spotify_client.py -v

# Run with verbose output
pytest -vv

# Use Makefile shortcuts
make test          # Run all tests
make coverage      # Run with coverage report
```

### Writing Tests

- Follow the existing test structure in `tests/`
- Use pytest fixtures for common setups
- Mock external dependencies (Spotify API, HTTP requests)
- Test both success and failure cases
- Aim for 90%+ code coverage on new code

## Architecture Guidelines

This project follows **SOLID principles** for maintainable, testable code:

### Key Architectural Concepts

1. **Interfaces**: Use abstract base classes from `spotichart.core.interfaces` and `spotichart.utils.interfaces`
2. **Dependency Injection**: Inject dependencies through constructors
3. **Factory Pattern**: Use `SpotifyServiceFactory` to create service instances
4. **Separation of Concerns**: Keep authentication, caching, and business logic separate

### Example: Adding a New Feature

```python
from spotichart.core.interfaces import ISpotifyClient
from spotichart.utils.interfaces import IConfiguration

class MyNewManager:
    """Manager that depends on abstractions, not concrete classes."""

    def __init__(self, client: ISpotifyClient, config: IConfiguration):
        self.client = client  # Depends on interface, not SpotifyClient
        self.config = config

    def do_something(self) -> None:
        # Use client interface methods
        playlists = self.client.current_user_playlists()
        # ...
```

### Code Organization

- **Core business logic**: `src/spotichart/core/`
- **Interfaces**: `src/spotichart/core/interfaces.py` and `src/spotichart/utils/interfaces.py`
- **Utilities**: `src/spotichart/utils/`
- **CLI**: `src/spotichart/cli/`
- **Tests**: `tests/` (mirror the src structure)

For more details, see:
- `docs/ARCHITECTURE.md` - Complete architecture documentation
- `docs/SOLID_GUIDE.md` - SOLID principles guide

## Commit Messages

Write clear, descriptive commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Add a detailed description if needed

### Good Examples

```
Add support for custom playlist descriptions
Fix error handling in scrape_top_songs function
Update README with installation instructions
```

### Bad Examples

```
Fixed stuff
Update
Changes
```

## Pull Request Process

1. **Update Documentation**: If you add features, update the README.md
2. **Test Thoroughly**: Ensure your changes work as expected
3. **Describe Changes**: Write a clear description of what your PR does
4. **Link Issues**: Reference any related issues in your PR description
5. **Be Responsive**: Respond to review comments promptly

## Bug Reports

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Error messages or logs
- Screenshots if applicable

## Feature Requests

When suggesting features:

- Explain the use case
- Describe how it should work
- Consider implementation challenges
- Be open to discussion

## Code of Conduct

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards other contributors

## Questions?

If you have questions, feel free to:

- Open an issue for discussion
- Comment on existing issues
- Reach out to the maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
