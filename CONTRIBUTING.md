# Contributing to Spotify Playlist Creator

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
git clone https://github.com/yourusername/spotify-playlist-creator.git
cd spotify-playlist-creator

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env
# Edit .env with your credentials
```

## Code Style

This project follows these coding standards:

- **PEP 8**: Follow Python's style guide
- **Type Hints**: Add type hints to all function signatures
- **Docstrings**: Document all functions, classes, and modules using Google-style docstrings
- **Line Length**: Maximum 100 characters per line

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

1. Your code works correctly
2. You've tested edge cases
3. No existing functionality is broken
4. Logging messages are appropriate

### Running Tests

```bash
# Run the application in test mode
python app.py
```

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
