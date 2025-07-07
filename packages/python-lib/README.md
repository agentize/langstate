# Khandhas

A Python library for khandhas application with support for development and production modes.

## Features

- **FastAPI-based server** with automatic API documentation
- **Development mode** with live reloading for debugging
- **Production mode** with compiled package support
- **Configurable** via environment variables or configuration files
- **Extensible** with custom routes and middleware
- **CLI interface** for easy deployment
- **Type hints** for better development experience

## Installation

### Prerequisites

**Important**: Always use a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (do this every time you work on the project)
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

### For Development

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install in development mode with live reloading
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### For Production

```bash
# Make sure virtual environment is activated (if using one)
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install from PyPI (when published)
pip install khandhas

# Or install from source
pip install .
```

## Quick Start

### Python API

```python
from khandhas import KhandhasServer, Config

# Create server with default configuration
server = KhandhasServer()

# Or with custom configuration
config = Config(
    host="0.0.0.0",
    port=8000,
    debug=True,
    reload=True
)
server = KhandhasServer(config)

# Run the server
server.run()
```

### Command Line Interface

```bash
# Run application with default settings
khandhas run

# Run in development mode with auto-reload
khandhas dev --reload

# Run with custom host and port
khandhas run --host 127.0.0.1 --port 8080

# Run with debug mode
khandhas run --debug --log-level DEBUG
```

### Environment Configuration

Create a `.env` file:

```env
KHANDHAS_HOST=0.0.0.0
KHANDHAS_PORT=8000
KHANDHAS_DEBUG=true
KHANDHAS_RELOAD=true
KHANDHAS_LOG_LEVEL=INFO
KHANDHAS_SECRET_KEY=your-secret-key-here
```

## Development vs Production Mode

### Development Mode

- **Live reloading**: Automatically restarts when code changes
- **Debug mode**: Detailed error messages and stack traces
- **Development dependencies**: Includes testing and linting tools

```python
# Development configuration
config = Config(
    debug=True,
    reload=True,
    log_level="DEBUG"
)
```

### Production Mode

- **Optimized performance**: No reloading, minimal logging
- **Security**: Error messages are sanitized
- **Compiled package**: Uses installed package instead of source

```python
# Production configuration
config = Config(
    debug=False,
    reload=False,
    log_level="INFO"
)
```

## API Endpoints

The server provides several built-in endpoints:

- `GET /health` - Health check endpoint
- `GET /api/v1/info` - Application information
- `POST /api/v1/echo` - Echo endpoint for testing

## Configuration

### Config Options

- `host`: Application host (default: "0.0.0.0")
- `port`: Application port (default: 8000)
- `debug`: Debug mode (default: False)
- `reload`: Auto-reload on changes (default: False)
- `log_level`: Logging level (default: "INFO")
- `cors_origins`: CORS origins (default: ["*"])
- `api_prefix`: API prefix (default: "/api/v1")
- `secret_key`: Secret key for JWT (default: "your-secret-key-here")

### Environment Variables

All configuration options can be set via environment variables with the `KHANDHAS_` prefix:

- `KHANDHAS_HOST`
- `KHANDHAS_PORT`
- `KHANDHAS_DEBUG`
- `KHANDHAS_RELOAD`
- `KHANDHAS_LOG_LEVEL`
- etc.

## Extending the Server

```python
from khandhas import KhandhasServer, Config

# Create server
server = KhandhasServer()

# Add custom startup handler
async def startup_handler():
    print("Application starting up...")

server.add_startup_handler(startup_handler)

# Add custom shutdown handler
async def shutdown_handler():
    print("Application shutting down...")

server.add_shutdown_handler(shutdown_handler)

# Get FastAPI app for custom routes
app = server.get_app()

@app.get("/custom")
async def custom_endpoint():
    return {"message": "Custom endpoint"}

# Run server
server.run()
```

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd khandhas/packages/python-lib

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 khandhas/

# Format code
black khandhas/

# Type checking
mypy khandhas/
```

## Testing

### Quick Test Commands

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=khandhas

# Run specific test file
pytest tests/test_server.py

# Run with verbose output
pytest -v

# Test installation
python -c "import khandhas; print(khandhas.__version__)"
```

### Comprehensive Testing

For detailed testing instructions, see [TESTING.md](TESTING.md).

**Development Environment Setup:**
```bash
# 1. Clone and setup
git clone <repo-url>
cd khandhas/packages/python-lib
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Run full test suite
pytest tests/ -v --cov=khandhas
```

**Code Quality Checks:**
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy khandhas/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Release Process

### Quick Release Commands

```bash
# 1. Pre-release checks
pytest && black --check . && flake8 .

# 2. Build package
python -m build

# 3. Test release
python -m twine upload --repository testpypi dist/*

# 4. Production release
python -m twine upload dist/*
```

### Full Release Guide

For complete release instructions, see [RELEASE.md](RELEASE.md).

**Version Management:**
- Follow [Semantic Versioning](https://semver.org/)
- Update version in `khandhas/__init__.py`
- Update `CHANGELOG.md` with release notes

**Release Checklist:**
- [ ] All tests pass: `pytest`
- [ ] Code formatted: `black --check .`
- [ ] No lint errors: `flake8 .`
- [ ] Type checking: `mypy khandhas/`
- [ ] Version updated
- [ ] Changelog updated
- [ ] Build package: `python -m build`
- [ ] Test on TestPyPI
- [ ] Release to PyPI
- [ ] Create git tag: `git tag v<version>`

## Documentation

- **[📚 Full Testing Guide](TESTING.md)** - Comprehensive testing instructions
- **[🚀 Release Guide](RELEASE.md)** - Step-by-step release process
- **[⚡ Quick Reference](QUICK_REFERENCE.md)** - Essential commands
- **[📋 Changelog](CHANGELOG.md)** - Version history and changes

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Changelog

### 0.1.0
- Initial release
- FastAPI-based server
- CLI interface
- Development and production modes
- Configuration management
- Basic API endpoints
