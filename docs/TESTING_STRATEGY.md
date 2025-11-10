# Testing Strategy for ShokoBot

## Overview

This document outlines the testing philosophy, approach, and best practices for the ShokoBot project. Our goal is to maintain high code quality through comprehensive testing while focusing on what matters most.

## Testing Philosophy

### What to Test (Priority Order)

1. **Business Logic** - Core functionality that changes behavior
2. **Data Validation** - Pydantic models, input validation
3. **Integration Points** - Service interactions, external APIs
4. **Edge Cases** - Error handling, boundary conditions
5. **Configuration** - Settings, environment variables

### What NOT to Test

- ❌ Third-party libraries (LangChain, ChromaDB, OpenAI)
- ❌ Simple getters/setters with no logic
- ❌ CLI output formatting (unless critical)
- ❌ Trivial pass-through functions

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── config/                        # Configuration tests
├── models/                        # Data model validation tests
├── services/                      # Service layer tests
├── utils/                         # Utility function tests
├── prompts/                       # Prompt template tests
└── integration/                   # End-to-end integration tests
```

### Test Types

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete workflows from start to finish

## Shared Test Fixtures

### Core Fixtures (`tests/conftest.py`)

We maintain a set of shared fixtures to ensure consistency across tests:

- **`mock_config`**: Mock ConfigService for testing without real config files
- **`mock_context`**: Mock AppContext with pre-configured dependencies
- **`sample_anime_data`**: Sample anime data for testing data processing
- **`sample_show_doc_dict`**: Sample ShowDoc data as dictionary
- **`temp_config_file`**: Temporary config file for file-based tests

These fixtures reduce duplication and make tests more maintainable.

## Testing Best Practices

### 1. Use Mocks for External Dependencies

Always mock external services to avoid:
- Real API calls that cost money
- Network dependencies that make tests flaky
- Slow tests that depend on external services

```python
# ✅ Good - Mock external services
@patch('services.vectorstore_service.OpenAIEmbeddings')
def test_with_mock(mock_embeddings):
    ...

# ❌ Bad - Real API calls in tests
def test_with_real_api():
    embeddings = OpenAIEmbeddings()  # Costs money!
```

### 2. Test One Thing Per Test

Each test should verify a single behavior or outcome:

```python
# ✅ Good - Single assertion
def test_title_cleaning():
    assert clean_title("  Test  ") == "Test"

# ❌ Bad - Multiple unrelated assertions
def test_everything():
    assert clean_title("  Test  ") == "Test"
    assert parse_date("2020-01-01") is not None
    assert batch_size > 0
```

### 3. Use Descriptive Test Names

Test names should clearly describe what is being tested:

```python
# ✅ Good - Clear what's being tested
def test_show_doc_rejects_end_year_before_begin_year():
    ...

# ❌ Bad - Unclear purpose
def test_years():
    ...
```

### 4. Follow the Arrange-Act-Assert (AAA) Pattern

The **AAA pattern** is a standard way to structure tests for clarity and consistency. It divides each test into three distinct sections:

- **Arrange**: Set up test data, mock objects, and preconditions
- **Act**: Execute the code under test (the function/method being tested)
- **Assert**: Verify the expected outcome

This pattern makes tests easier to read and understand:

```python
def test_example():
    # Arrange - Set up test data and preconditions
    data = {"key": "value"}
    expected = "processed_value"
    
    # Act - Execute the code under test
    result = process(data)
    
    # Assert - Verify the expected outcome
    assert result == expected
```

### 5. Test Edge Cases and Error Conditions

Don't just test the happy path:

```python
def test_parse_datetime_valid():
    """Test valid datetime parsing."""
    result = parse_datetime("2020-01-15 12:30:45")
    assert result is not None

def test_parse_datetime_invalid():
    """Test invalid datetime handling."""
    result = parse_datetime("invalid-date")
    assert result is None

def test_parse_datetime_none():
    """Test None input returns None."""
    result = parse_datetime(None)
    assert result is None
```

### 6. Use Parametrized Tests for Similar Cases

When testing multiple inputs with the same logic:

```python
@pytest.mark.parametrize("input,expected", [
    ("  test  ", "test"),
    ("TEST", "test"),
    ("", ""),
    (None, None),
])
def test_normalize_string(input, expected):
    assert normalize(input) == expected
```

### 7. Keep Tests Independent

Tests should not depend on each other or share state:

```python
# ✅ Good - Each test is independent
def test_create_user():
    user = create_user("test")
    assert user.name == "test"

def test_delete_user():
    user = create_user("test")
    delete_user(user)
    assert get_user("test") is None

# ❌ Bad - Tests depend on execution order
def test_create_user():
    global user
    user = create_user("test")

def test_delete_user():
    delete_user(user)  # Depends on previous test
```

## Coverage Goals

### Target Coverage Levels

- **Overall Project**: 90%+
- **Critical Business Logic**: 95%+
- **Data Models**: 95%+
- **Services**: 90%+
- **Utilities**: 90%+
- **Integration Tests**: 80%+

### Coverage Philosophy

Coverage is a useful metric but not the only goal:
- 100% coverage doesn't guarantee bug-free code
- Focus on testing critical paths and edge cases
- Prioritize meaningful tests over coverage numbers
- Use coverage reports to identify untested code paths

## Running Tests

### Basic Commands

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov

# Run with detailed coverage report
poetry run pytest --cov --cov-report=term-missing

# Run specific test file
poetry run pytest tests/models/test_show_doc.py

# Run specific test class
poetry run pytest tests/models/test_show_doc.py::TestShowDoc

# Run specific test function
poetry run pytest tests/models/test_show_doc.py::test_show_doc_creation

# Run with verbose output
poetry run pytest -v

# Run and stop on first failure
poetry run pytest -x

# Run only failed tests from last run
poetry run pytest --lf

# Run tests matching a pattern
poetry run pytest -k "test_parse"
```

### Coverage Reports

```bash
# Generate HTML coverage report
poetry run pytest --cov --cov-report=html

# View coverage for specific module
poetry run pytest --cov=services/ingest_service --cov-report=term-missing

# Generate coverage report without running tests (if .coverage exists)
poetry run coverage report
```

## Continuous Integration

### Pre-commit Hooks

The project uses pre-commit hooks to maintain code quality and ensure all tests pass before committing. Configured hooks include:

- **Testing**: Pytest runs all tests automatically before each commit
- **Code formatting**: Ruff formatter for consistent style
- **Linting**: Ruff linter with auto-fix
- **Type checking**: MyPy for static type analysis
- **Security scanning**: Bandit for security vulnerabilities
- **File checks**: Trailing whitespace, YAML/JSON validation, etc.

Tests run automatically via the pytest hook configured in `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: poetry run pytest
      language: system
      pass_filenames: false
      always_run: true
```

This ensures that all tests pass before code is committed, catching issues early in the development cycle.

### CI/CD Pipeline

For production deployments, integrate testing into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run tests with coverage
        run: poetry run pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Testing Workflow

### Development Cycle

1. **Write failing test** - Define expected behavior
2. **Implement feature** - Write minimal code to pass test
3. **Refactor** - Improve code while keeping tests green
4. **Run coverage** - Identify untested code paths
5. **Add edge case tests** - Cover error conditions

### Code Review Checklist

- [ ] All new code has corresponding tests
- [ ] Tests follow AAA pattern
- [ ] Test names are descriptive
- [ ] Edge cases and error conditions are tested
- [ ] External dependencies are mocked
- [ ] Coverage meets or exceeds 90%
- [ ] All tests pass locally
- [ ] No flaky or intermittent test failures

## Common Testing Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Testing Exceptions

```python
def test_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        process_invalid_data()
```

### Testing with Temporary Files

```python
def test_file_processing(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text('{"key": "value"}')
    result = process_file(test_file)
    assert result is not None
```

### Testing with Environment Variables

```python
def test_env_override(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    config = load_config()
    assert config.api_key == "test-key"
```

## Troubleshooting

### Common Issues

**Tests pass locally but fail in CI**
- Check for environment-specific dependencies
- Ensure all fixtures are properly isolated
- Verify no hardcoded paths or assumptions

**Flaky tests**
- Avoid time-dependent tests
- Mock external services properly
- Ensure tests don't depend on execution order

**Slow tests**
- Mock expensive operations (API calls, database queries)
- Use smaller test datasets
- Consider parallel test execution with pytest-xdist

**Low coverage on error paths**
- Add tests for exception handling
- Test invalid inputs and edge cases
- Use coverage reports to identify missing paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Effective Python Testing](https://realpython.com/pytest-python-testing/)

## Summary

Our testing strategy emphasizes:
- **Quality over quantity**: Meaningful tests that catch real bugs
- **Maintainability**: Clear, well-organized tests that are easy to update
- **Coverage**: 90%+ coverage with focus on critical paths
- **Best practices**: AAA pattern, mocking, descriptive names
- **Automation**: Pre-commit hooks and CI/CD integration

By following these guidelines, we ensure that ShokoBot remains reliable, maintainable, and easy to extend.
