# LangState

A modern, lightweight Python library for building FastAPI-based web applications with built-in configuration management, CLI tools, and development utilities.

## Features

- 🚀 **FastAPI Integration**: Built on top of FastAPI for high-performance web APIs
- ⚙️ **Configuration Management**: Environment-based configuration with Pydantic validation
- 🛠️ **CLI Tools**: Command-line interface for development and production
- 🔧 **Development Tools**: Live reload, debugging, and development server
- 📦 **Production Ready**: Optimized for production deployments
- 🧪 **Well Tested**: Comprehensive test suite with 43+ tests
- 🔒 **Type Safe**: Full type annotations and mypy support

## Quick Start

### Installation

```bash
# Install from PyPI
pip install langstate

# Or for development, clone and install locally:
git clone <repository-url>
cd langstate/packages/python-lib

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install in development mode
pip install -e ".[dev]"
```

### Basic Usage

**Note**: Always activate your virtual environment first if using local development:

```bash
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

```python
from langstate import LangStateServer, Config

# Create configuration
config = Config(
    host="127.0.0.1",
    port=8000,
    debug=True
)

# Create and run server
server = LangStateServer(config)
server.run()
```

### Using CLI

```bash
# Make sure virtual environment is activated (for local development)
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Run in development mode
langstate dev

# Run in production mode
langstate run --host 0.0.0.0 --port 8000

# Show version
langstate version
```

## Documentation

- [📚 Full Documentation](packages/python-lib/README.md)
- [🧪 Testing Guide](packages/python-lib/TESTING.md)
- [🚀 Release Guide](packages/python-lib/RELEASE.md)
- [📋 Changelog](packages/python-lib/CHANGELOG.md)

## Development

### Quick Setup (Recommended)

For the fastest setup, use the provided setup scripts:

```bash
# Linux/Mac
./setup.sh

# Windows
setup.bat
```

These scripts will:

- Create a virtual environment
- Install all dependencies
- Verify the installation
- Run a quick test
- Show you next steps

### Manual Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd langstate

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 4. Install the package for development
cd packages/python-lib
pip install -e ".[dev]"

# 5. Run tests to verify setup
pytest

# 6. Try the sample app
cd ../../sample-app
python main.py
```

### Project Structure

This is a monorepo containing:

- `packages/python-lib/` - The main Python package
- `packages/node-lib/` - Node.js client library
- `packages/shared/` - Shared utilities
- `sample-app/` - Example application

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.
