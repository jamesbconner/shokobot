# Shokobot Setup Guide

## Quick Start

### 1. Run Setup Script
```bash
./setup.sh
```

This will:
- Check Python version (3.12+ required)
- Detect and use Poetry or uv
- Install all dependencies
- Create .env from template
- Install pre-commit hooks
- Create necessary directories

### 2. Configure Environment
Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY='sk-...'
```

### 3. Prepare Data
Place your anime data JSON file at:
```
input/tvshows.json
```

### 4. Ingest Data
```bash
make ingest
# or
poetry run shokobot-ingest
```

### 5. Start Querying
```bash
make rag
# or
poetry run shokobot-rag --repl
```

## Development Workflow

### Using Make Commands

```bash
# Install dependencies
make install-dev

# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Security scan
make security

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all checks
make check

# Run pre-commit hooks
make pre-commit
```

### Using Poetry Directly

```bash
# Install dependencies
poetry install --with dev

# Run commands
poetry run shokobot-ingest
poetry run shokobot-rag --repl

# Run tools
poetry run ruff format .
poetry run mypy .
poetry run pytest
```

### Using uv (Alternative)

```bash
# Create virtual environment
uv venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Run commands
python main_ingest.py
python main_rag.py --repl
```

## Pre-commit Hooks

Pre-commit hooks automatically run on every commit:
- Trailing whitespace removal
- End-of-file fixing
- YAML/JSON/TOML validation
- Ruff formatting and linting
- MyPy type checking
- Bandit security scanning

### Manual Execution
```bash
pre-commit run --all-files
```

### Skip Hooks (Not Recommended)
```bash
git commit --no-verify
```

## Configuration Files

### pyproject.toml
Main project configuration:
- Dependencies (production and dev)
- Poetry scripts
- Ruff configuration
- MyPy configuration
- Pytest configuration
- Coverage configuration
- Bandit configuration

### .pre-commit-config.yaml
Pre-commit hook configuration:
- Code formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Security scanning (bandit)
- File validation

### resources/config.json
Application configuration:
- ChromaDB settings
- OpenAI model selection
- Batch sizes
- Logging levels

### .env
Environment variables:
- API keys
- Configuration overrides

## Troubleshooting

### Poetry Not Found
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### uv Not Found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python Version Issues
Ensure Python 3.12+ is installed:
```bash
python --version
```

### Import Errors
Ensure you're in the virtual environment:
```bash
poetry shell
# or
source .venv/bin/activate
```

### Pre-commit Hook Failures
Run manually to see detailed errors:
```bash
pre-commit run --all-files
```

### Type Checking Errors
MyPy is configured strictly. To see all errors:
```bash
mypy . --show-error-codes
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      - name: Install dependencies
        run: poetry install --with dev
      - name: Run checks
        run: |
          poetry run ruff check .
          poetry run mypy .
          poetry run bandit -r services models utils
          poetry run pytest --cov
```

## Best Practices

1. **Always run tests before committing**
   ```bash
   make test
   ```

2. **Format code before committing**
   ```bash
   make format
   ```

3. **Run all checks periodically**
   ```bash
   make check
   ```

4. **Keep dependencies updated**
   ```bash
   make update
   ```

5. **Use type hints everywhere**
   - All functions must have return type annotations
   - All parameters must have type hints

6. **Write docstrings**
   - Use Google-style docstrings
   - Document parameters, returns, and exceptions

7. **Handle errors gracefully**
   - Use specific exception types
   - Provide informative error messages
   - Log errors appropriately

8. **Test your changes**
   - Write tests for new features
   - Aim for 90%+ code coverage
   - Test edge cases
