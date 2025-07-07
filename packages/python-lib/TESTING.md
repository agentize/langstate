# Testing Guide

This guide provides comprehensive instructions for testing the Khandhas Python library.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [CI/CD Testing](#cicd-testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before running tests, ensure you have:

- Python 3.9+ installed
- Git installed
- Virtual environment support (venv or conda)

## Setting Up the Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/khandhas.git
cd khandhas/packages/python-lib
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n khandhas python=3.11
conda activate khandhas
```

### 3. Install Dependencies

```bash
# Install package in development mode with dev dependencies
pip install -e ".[dev]"

# Or install manually
pip install -e .
pip install pytest pytest-asyncio pytest-cov black flake8 mypy pre-commit
```

### 4. Verify Installation

```bash
# Test package import
python -c "import khandhas; print('✅ Package imported successfully')"

# Test CLI
khandhas version
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=khandhas

# Run tests with coverage report
pytest --cov=khandhas --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test function
pytest tests/test_config.py::test_server_config_defaults

# Run tests matching a pattern
pytest -k "config"
```

### Advanced Testing Options

```bash
# Run tests in parallel (if pytest-xdist is installed)
pytest -n auto

# Run tests with detailed output
pytest -v --tb=short

# Run tests and stop on first failure
pytest -x

# Run tests with coverage and generate HTML report
pytest --cov=khandhas --cov-report=html --cov-report=term-missing

# Run tests with specific Python version (if using tox)
tox -e py39
tox -e py311
```

### Performance Testing

```bash
# Run tests with timing information
pytest --durations=10

# Run tests with memory profiling (if pytest-memray is installed)
pytest --memray

# Run stress tests (if available)
pytest tests/test_stress.py -v
```

## Test Types

### 1. Unit Tests

Test individual components in isolation:

```bash
# Configuration tests
pytest tests/test_config.py

# Server tests
pytest tests/test_server.py

# Utility tests
pytest tests/test_utils.py

# Model tests
pytest tests/test_models.py

# CLI tests
pytest tests/test_cli.py
```

### 2. Integration Tests

Test component interactions:

```bash
# Import tests
pytest tests/test_imports.py

# End-to-end tests
pytest tests/test_integration.py  # If available
```

### 3. Manual Testing

Test the sample application:

```bash
# Navigate to sample app
cd ../../sample-app

# Run sample app in development mode
python main.py --mode dev

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/info
```

## Writing Tests

### Test Structure

```python
"""Test module docstring."""

import pytest
from unittest.mock import Mock, patch
from khandhas import KhandhasServer, Config


def test_feature_basic():
    """Test basic functionality."""
    # Arrange
    config = Config(debug=True)
    server = KhandhasServer(config)
    
    # Act
    result = server.get_app()
    
    # Assert
    assert result is not None


@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    # Arrange
    server = KhandhasServer()
    
    # Act
    result = await server.start()
    
    # Assert
    assert result is not None


def test_feature_with_mock():
    """Test with mocking."""
    with patch('khandhas.server.uvicorn') as mock_uvicorn:
        server = KhandhasServer()
        server.run()
        mock_uvicorn.run.assert_called_once()


@pytest.fixture
def sample_config():
    """Fixture for test configuration."""
    return Config(
        host="127.0.0.1",
        port=8888,
        debug=True
    )


def test_with_fixture(sample_config):
    """Test using fixture."""
    server = KhandhasServer(sample_config)
    assert server.config.host == "127.0.0.1"
```

### Test Best Practices

1. **Use descriptive test names**: `test_config_validates_port_range`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures for common setup**: `@pytest.fixture`
4. **Mock external dependencies**: Use `unittest.mock`
5. **Test edge cases**: Invalid inputs, boundary conditions
6. **Keep tests focused**: One concept per test
7. **Use parametrized tests**: `@pytest.mark.parametrize`

## Test Coverage

### Generate Coverage Reports

```bash
# Terminal report
pytest --cov=khandhas --cov-report=term-missing

# HTML report
pytest --cov=khandhas --cov-report=html
open htmlcov/index.html  # View in browser

# XML report (for CI/CD)
pytest --cov=khandhas --cov-report=xml
```

### Coverage Targets

- **Minimum acceptable**: 80%
- **Target**: 90%+
- **Critical modules**: 95%+

### Check Coverage

```bash
# Check current coverage
pytest --cov=khandhas --cov-fail-under=80

# Generate coverage badge
coverage-badge -o coverage.svg
```

## CI/CD Testing

### GitHub Actions

The project includes a GitHub Actions workflow that runs tests automatically:

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest --cov=khandhas --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Local CI Simulation

```bash
# Run tests like CI does
python -m pytest tests/ -v --cov=khandhas --cov-report=xml

# Run linting
black --check .
flake8 .
mypy khandhas/

# Run pre-commit hooks
pre-commit run --all-files
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'khandhas'
# Solution: Install in development mode
pip install -e .
```

#### 2. Test Discovery Issues

```bash
# Error: No tests found
# Solution: Run from project root
cd packages/python-lib
pytest
```

#### 3. FastAPI Not Found

```bash
# Error: RuntimeError: FastAPI is not installed
# Solution: Install with dev dependencies
pip install -e ".[dev]"
```

#### 4. Port Already in Use

```bash
# Error: Address already in use
# Solution: Use different port or kill process
lsof -ti:8000 | xargs kill -9
```

### Debug Mode

```bash
# Run tests with debug output
pytest -v --tb=long --capture=no

# Run single test with print statements
pytest tests/test_config.py::test_server_config_defaults -s

# Use Python debugger
pytest --pdb
```

### Performance Issues

```bash
# Check slow tests
pytest --durations=10

# Profile memory usage
pytest --memray tests/

# Run subset of tests
pytest tests/test_config.py tests/test_models.py
```

## Test Environment Variables

Set these environment variables for testing:

```bash
# For development
export KHANDHAS_DEBUG=true
export KHANDHAS_LOG_LEVEL=DEBUG

# For CI/CD
export KHANDHAS_TEST_MODE=true
export KHANDHAS_DISABLE_RELOAD=true
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)

---

For more information, see the [main README](README.md) or [Release Guide](RELEASE.md).
