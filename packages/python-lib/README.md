# LangState

A Python library for langstate application with support for development and production modes.

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
pip install langstate

# Or install from source
pip install .
```

## Quick Start

### Python API

```python
from langstate import LangStateServer, Config

# Basic server
server = LangStateServer()

# Or with custom configuration
config = Config(
    host="0.0.0.0",
    port=8000,
    debug=True,
    reload=True
)
server = LangStateServer(config)

# Run the server
server.run()
```

### Command Line Interface

```bash
# Run in production mode
langstate run

# Run in development mode with reload
langstate dev --reload

# Custom host and port
langstate run --host 127.0.0.1 --port 8080

# Debug mode with verbose logging
langstate run --debug --log-level DEBUG
```

### Environment Configuration

Create a `.env` file:

```env
LANGSTATE_HOST=0.0.0.0
LANGSTATE_PORT=8000
LANGSTATE_DEBUG=true
LANGSTATE_RELOAD=true
LANGSTATE_LOG_LEVEL=INFO
LANGSTATE_SECRET_KEY=your-secret-key-here
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

All configuration options can be set via environment variables with the `LANGSTATE_` prefix:

- `LANGSTATE_HOST`
- `LANGSTATE_PORT`
- `LANGSTATE_DEBUG`
- `LANGSTATE_RELOAD`
- `LANGSTATE_LOG_LEVEL`
- etc.

## Extending the Server

```python
from langstate import LangStateServer, Config

# Create and run server
server = LangStateServer()

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
cd langstate/packages/python-lib

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 langstate/

# Format code
black langstate/

# Type checking
mypy langstate/
```

## Testing

### Quick Test Commands

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=langstate

# Run specific test file
pytest tests/test_server.py

# Run with verbose output
pytest -v

# Test installation
python -c "import langstate; print(langstate.__version__)"
```

### Comprehensive Testing

For detailed testing instructions, see [TESTING.md](TESTING.md).

**Development Environment Setup:**

```bash
# 1. Clone and setup
git clone <repo-url>
cd langstate/packages/python-lib
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Run full test suite
pytest tests/ -v --cov=langstate
```

**Code Quality Checks:**

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy langstate/

# Run all pre-commit hooks
pre-commit run --all-files
```

## x-sup constraints in OpenAPI YAML

LangState extends OpenAPI schemas with an `x-sup` section to declare inter-field constraints.

Recommended key for specifying the prerequisite/source field is `source` (or `from`).
While `on` is also supported for backwards compatibility, some YAML parsers may
coerce `on/off/yes/no` into booleans under YAML 1.1 rules. This library includes a
patched loader to preserve such keys as strings, but using `source` is clearer and safer.

Example (excerpt):

```yaml
components:
    schemas:
        Registration:
            type: object
            properties:
                event:
                    $ref: "#/components/schemas/Event"
                    x-sup:
                        constraints:
                            - source: "registrant"
                                status:
                                    allowed: ["validated"]

                guests:
                    type: array
                    items:
                        allOf:
                            - $ref: "#/components/schemas/Guest"
                            - type: object
                                x-sup:
                                    constraints:
                                        - source: "event"
                                            status:
                                                allowed: ["edited"]
                                            prompt: "Guests can only be added when the event is confirmed."
                                        - source: "registrant"
                                            status:
                                                allowed: ["validated"]
```

Accepted synonyms for the prerequisite/source key: `source`, `from`, `on`, `prereq`, `prereq_id`, `src`.
The loader will normalize these and add corresponding constraint edges in the Schema DAG.

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
- Update version in `langstate/__init__.py`
- Update `CHANGELOG.md` with release notes

**Release Checklist:**

- [ ] All tests pass: `pytest`
- [ ] Code formatted: `black --check .`
- [ ] No lint errors: `flake8 .`
- [ ] Type checking: `mypy langstate/`
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
