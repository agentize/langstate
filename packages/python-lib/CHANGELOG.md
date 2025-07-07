# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-07-06

### Added
- Initial release of the `khandhas` Python library
- FastAPI-based web framework with configurable settings
- Command-line interface for running applications
- Comprehensive test suite with pytest
- Pre-commit hooks for code quality
- CI/CD pipeline with GitHub Actions
- Complete documentation and examples
- Sample application demonstrating usage

### Changed
- **BREAKING**: Renamed package from `khandhas_server` to `khandhas`
- **BREAKING**: Renamed `ServerConfig` to `Config` for broader applicability
- **BREAKING**: Updated import paths and references throughout codebase
- **BREAKING**: Minimum Python version requirement updated from 3.8 to 3.9
- Updated dependencies to follow PyPI best practices with upper bounds
- Improved error handling and validation
- Enhanced CLI with better subcommand structure

### Technical Details
- Python version support: 3.9 - 3.13
- Dependencies now use version ranges (e.g., `fastapi>=0.104.0,<1.0.0`)
- Fixed type annotations for Python 3.9+ compatibility
- Improved Pydantic v2 configuration with proper validation
- Enhanced boolean conversion utilities
- Better test coverage and error handling
- Updated build system to use modern setuptools

### Migration Guide
If upgrading from the old `khandhas_server` package:

1. Update imports:
   ```python
   # Old
   from khandhas_server import KhandhasServer, ServerConfig
   
   # New
   from khandhas import KhandhasServer, Config
   ```

2. Update configuration:
   ```python
   # Old
   config = ServerConfig(host="localhost")
   
   # New
   config = Config(host="localhost")
   ```

3. Update CLI usage:
   ```bash
   # Old
   khandhas-server run
   
   # New
   khandhas run
   ```

### Development
- Install in development mode: `pip install -e .`
- Run tests: `pytest`
- Run linting: `pre-commit run --all-files`
- Build package: `python -m build`

### Deployment
- Package is ready for PyPI publication
- Supports both development (live reload) and production modes
- Includes comprehensive CI/CD pipeline
- Full documentation and examples provided
