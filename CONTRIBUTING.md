# Contributing to ShokoBot

Thank you for your interest in contributing to ShokoBot! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment for all contributors

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry or uv for dependency management
- Git for version control
- OpenAI API key for testing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/jamesbconner/shokobot.git
   cd shokobot
   ```

2. **Install Dependencies**
   ```bash
   poetry install --with dev
   # or
   uv sync --all-extras
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Set Up Environment**
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Your Changes

- Write clean, readable code following the project style
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Run Quality Checks

Before committing, ensure all checks pass:

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check . --fix

# Type check
poetry run mypy services/ utils/ models/ --ignore-missing-imports

# Run tests with coverage
poetry run pytest --cov --cov-fail-under=90

# Security scan
poetry run bandit -r services/ utils/ models/

# Or run all pre-commit hooks
poetry run pre-commit run --all-files
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new anime search feature"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub using the PR template.

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Use type hints for all functions and methods
- Write Google-style docstrings
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### Example

```python
def search_anime(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search for anime by title.

    Args:
        query: Search query string.
        limit: Maximum number of results to return.

    Returns:
        List of anime dictionaries with metadata.

    Raises:
        ValueError: If query is empty or limit is invalid.
    """
    if not query:
        raise ValueError("Query cannot be empty")

    # Implementation here
    return results
```

## Testing Guidelines

### Writing Tests

- Use pytest for all tests
- Follow AAA pattern (Arrange, Act, Assert)
- Write descriptive test names
- Test both happy paths and error cases
- Mock external dependencies (OpenAI, MCP server, file system)

### Test Structure

```python
def test_search_anime_returns_results(mock_context: Mock) -> None:
    """Test that search_anime returns valid results."""
    # Arrange
    query = "Cowboy Bebop"
    expected_count = 5

    # Act
    results = search_anime(query, limit=expected_count)

    # Assert
    assert len(results) == expected_count
    assert all("title" in r for r in results)
```

### Coverage Requirements

- Maintain overall coverage ≥ 90%
- New code should have ≥ 95% coverage
- Critical paths must be fully tested

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Coverage remains ≥ 90%
- [ ] Code is formatted with ruff
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Checklist

Use the PR template and ensure:

1. **Description** - Clear explanation of changes
2. **Type of Change** - Marked appropriately
3. **Related Issues** - Linked if applicable
4. **Testing** - Describe tests performed
5. **Checklist** - All items checked

### Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer review required
3. Address review feedback
4. Squash commits if requested
5. Maintainer will merge when approved

## Reporting Issues

### Bug Reports

Use the bug report template and include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error messages/logs

### Feature Requests

Use the feature request template and include:
- Problem statement
- Proposed solution
- Use cases
- Implementation ideas (optional)

## Documentation

### Code Documentation

- All public functions/classes need docstrings
- Use Google-style docstring format
- Include examples for complex functionality
- Document parameters, returns, and exceptions

### Project Documentation

- Update README.md for user-facing changes
- Update docs/ for architecture changes
- Keep examples up to date
- Document breaking changes

## Questions?

- Open a discussion on GitHub
- Check existing issues and PRs
- Review the documentation in docs/

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to ShokoBot! 🎉
