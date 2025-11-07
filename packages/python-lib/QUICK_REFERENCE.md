# Quick Reference Guide

Essential commands for testing and releasing the Khandhas package.

## 🔍 Quick Verification

```bash
# Run verification script to check everything
python verify.py

# This checks:
# - Python version compatibility
# - Package installation
# - Development environment
# - CLI functionality
# - Test execution
# - Code quality
```

## 🧪 Testing Commands

### Setup Development Environment
```bash
# Clone and setup
git clone <repo-url>
cd khandhas/packages/python-lib

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install in development mode
pip install -e ".[dev]"

# Verify setup
python -c "import khandhas; print('✅ Setup complete')"
```

**Important**: Always activate your virtual environment before running any commands:
```bash
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows
```

### Run Tests
```bash
# Basic test run
pytest

# With coverage
pytest --cov=khandhas

# Verbose output
pytest -v

# Specific test file
pytest tests/test_config.py

# Stop on first failure
pytest -x
```

### Code Quality
```bash
# Format code
black .

# Check formatting
black --check .

# Lint code
flake8 .

# Type checking
mypy khandhas/

# All quality checks
pre-commit run --all-files
```

## 🚀 Release Commands

### Pre-Release Checks
```bash
# Run all tests
pytest tests/ -v --cov=khandhas

# Quality checks
black --check . && flake8 . && mypy khandhas/

# Test CLI
khandhas version
```

### Build Package
```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info/

# Build distributions
python -m build

# Verify package
python -m twine check dist/*
```

### Test Release
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ khandhas
```

### Production Release
```bash
# Upload to PyPI
python -m twine upload dist/*

# Create git tag
git tag v0.1.0
git push origin v0.1.0

# Test install from PyPI
pip install khandhas
```

## 📋 Quick Checklist

### Before Release
- [ ] `pytest` - All tests pass
- [ ] `black --check .` - Code formatted
- [ ] `flake8 .` - No linting errors
- [ ] Update version in `khandhas/__init__.py`
- [ ] Update `CHANGELOG.md`

### Release Process
- [ ] `python -m build` - Build package
- [ ] `python -m twine check dist/*` - Verify package
- [ ] `python -m twine upload --repository testpypi dist/*` - Test upload
- [ ] `python -m twine upload dist/*` - Production upload
- [ ] `git tag v<version>` - Tag release

### After Release
- [ ] Test installation: `pip install khandhas`
- [ ] Create GitHub release
- [ ] Update documentation

## 🔧 Troubleshooting

### Common Fixes
```bash
# Import errors
pip install -e .

# Test discovery issues
cd packages/python-lib && pytest

# Dependency issues
pip install -e ".[dev]"

# Permission errors
pip install --user -e .
```

### Debug Commands
```bash
# Verbose test output
pytest -v --tb=long

# Check package contents
python -m zipfile -l dist/*.whl

# Verify installation
python -c "import khandhas; print(khandhas.__version__)"
```

## 📖 Documentation Links

- [📚 Full Testing Guide](TESTING.md)
- [🚀 Complete Release Guide](RELEASE.md)
- [📋 Changelog](CHANGELOG.md)
- [📖 Main README](README.md)

## x-sup Constraint Snippet

Use `source` (or `from`) to declare constraint prerequisites in your OpenAPI YAML:

```yaml
x-sup:
	constraints:
		- source: "registrant"
			status:
				allowed: ["validated"]
```

Synonyms supported: `source`, `from`, `on`, `prereq`, `prereq_id`, `src`.
