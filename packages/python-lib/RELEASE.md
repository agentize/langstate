# Release Guide

This guide provides step-by-step instructions for releasing the Khandhas Python library to PyPI and managing releases.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Release Checklist](#pre-release-checklist)
- [Version Management](#version-management)
- [Building the Package](#building-the-package)
- [Testing the Release](#testing-the-release)
- [Publishing to PyPI](#publishing-to-pypi)
- [Post-Release Tasks](#post-release-tasks)
- [Release Automation](#release-automation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Required Tools

```bash
# Install build tools
pip install --upgrade pip setuptools wheel build twine

# Install development dependencies
pip install -e ".[dev]"
```

### 2. PyPI Account Setup

1. **Create PyPI account**: [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **Create TestPyPI account**: [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
3. **Generate API tokens**:
   - PyPI: Account settings → API tokens → Add API token
   - TestPyPI: Account settings → API tokens → Add API token

### 3. Configure PyPI Credentials

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-api-token-here
```

Or use environment variables:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

## Pre-Release Checklist

### ✅ Code Quality

```bash
# 1. Run all tests
pytest tests/ -v --cov=khandhas

# 2. Check code formatting
black --check .

# 3. Run linting
flake8 .

# 4. Type checking
mypy khandhas/

# 5. Run pre-commit hooks
pre-commit run --all-files

# 6. Security check (optional)
bandit -r khandhas/
```

### ✅ Documentation

- [ ] Update README.md with new features
- [ ] Update CHANGELOG.md with release notes
- [ ] Verify all docstrings are up to date
- [ ] Check that examples work
- [ ] Update version numbers in documentation

### ✅ Dependencies

- [ ] Review and update dependency versions
- [ ] Ensure compatibility with supported Python versions
- [ ] Test with minimum required versions
- [ ] Check for security vulnerabilities

### ✅ Testing

```bash
# Test with different Python versions (if using tox)
tox

# Test installation from source
pip install .

# Test CLI commands
khandhas version
khandhas --help

# Test sample application
cd ../../sample-app
python main.py --help
```

## Version Management

### Semantic Versioning

Follow [Semantic Versioning (SemVer)](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Update Version

1. **Update version in `khandhas/__init__.py`**:

```python
__version__ = "0.2.0"
```

2. **Update version in `pyproject.toml`**:

```toml
[project]
version = "0.2.0"
```

3. **Update version in `setup.py`** (if using):

```python
version="0.2.0",
```

### Create Release Notes

Update `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-07-06

### Added
- New feature X
- New configuration option Y

### Changed
- Improved performance of Z
- Updated dependency versions

### Fixed
- Fixed bug in component A
- Resolved issue with B

### Deprecated
- Feature C will be removed in v1.0.0

### Removed
- Removed deprecated feature D

### Security
- Fixed security issue in authentication
```

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info/

# Or use git clean (be careful!)
git clean -fdx
```

### 2. Build Distribution Packages

```bash
# Build source distribution and wheel
python -m build

# Verify build output
ls -la dist/
# Should see: khandhas-0.2.0.tar.gz and khandhas-0.2.0-py3-none-any.whl
```

### 3. Verify Package Contents

```bash
# Check wheel contents
python -m zipfile -l dist/khandhas-0.2.0-py3-none-any.whl

# Check source distribution
tar -tzf dist/khandhas-0.2.0.tar.gz

# Verify package metadata
python -m twine check dist/*
```

## Testing the Release

### 1. Test Local Installation

```bash
# Create fresh virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from built wheel
pip install dist/khandhas-0.2.0-py3-none-any.whl

# Test basic functionality
python -c "import khandhas; print(khandhas.__version__)"
khandhas version

# Clean up
deactivate
rm -rf test-env
```

### 2. Upload to TestPyPI

```bash
# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ khandhas==0.2.0

# Test the installed package
python -c "import khandhas; print('✅ Package works from TestPyPI')"
```

## Publishing to PyPI

### 1. Final Checks

```bash
# Ensure you're on the main branch
git branch

# Ensure working directory is clean
git status

# Ensure all tests pass
pytest

# Verify package metadata
python -m twine check dist/*
```

### 2. Upload to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Verify upload
# Visit: https://pypi.org/project/khandhas/
```

### 3. Test Installation from PyPI

```bash
# Create fresh environment
python -m venv release-test
source release-test/bin/activate

# Install from PyPI
pip install khandhas==0.2.0

# Test functionality
python -c "import khandhas; print(f'✅ Version {khandhas.__version__} works from PyPI')"
khandhas version

# Clean up
deactivate
rm -rf release-test
```

## Post-Release Tasks

### 1. Git Tagging

```bash
# Create and push git tag
git tag v0.2.0
git push origin v0.2.0

# Or create annotated tag with message
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### 2. GitHub Release

1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Choose tag: `v0.2.0`
4. Release title: `Khandhas v0.2.0`
5. Description: Copy from CHANGELOG.md
6. Attach build artifacts (optional)
7. Click "Publish release"

### 3. Update Documentation

```bash
# Update main branch with post-release changes
git add .
git commit -m "chore: post-release updates for v0.2.0"
git push origin main
```

### 4. Announce Release

- [ ] Update project README
- [ ] Post on social media
- [ ] Update package documentation
- [ ] Notify users/stakeholders

## Release Automation

### GitHub Actions Release Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip build twine
        pip install -e ".[dev]"
    
    - name: Run tests
      run: pytest
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: python -m twine check dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: python -m twine upload dist/*
    
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
```

### Automated Version Bumping

Using `bump2version`:

```bash
# Install bump2version
pip install bump2version

# Create .bumpversion.cfg
cat > .bumpversion.cfg << EOF
[bumpversion]
current_version = 0.1.0
commit = True
tag = True

[bumpversion:file:khandhas/__init__.py]
[bumpversion:file:pyproject.toml]
[bumpversion:file:setup.py]
EOF

# Bump version
bump2version patch  # 0.1.0 → 0.1.1
bump2version minor  # 0.1.1 → 0.2.0
bump2version major  # 0.2.0 → 1.0.0
```

## Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Error: No module named 'setuptools'
pip install --upgrade setuptools wheel

# Error: Package has invalid metadata
python -m twine check dist/*

# Error: Missing files in distribution
# Check MANIFEST.in or pyproject.toml [tool.setuptools.package-data]
```

#### 2. Upload Issues

```bash
# Error: Invalid credentials
# Check ~/.pypirc or environment variables

# Error: File already exists
# Version already published, increment version

# Error: Package name taken
# Choose different name or request name transfer
```

#### 3. Installation Issues

```bash
# Error: No matching distribution found
# Check package name and version

# Error: Dependency conflicts
# Review requirements and version constraints

# Error: Python version incompatibility
# Check python_requires in setup configuration
```

### Debug Commands

```bash
# Check package metadata
python setup.py check --metadata --strict

# Verbose build
python -m build --verbose

# Verbose upload
python -m twine upload --verbose dist/*

# Check installed package
pip show khandhas
pip list | grep khandhas
```

### Rollback Procedures

```bash
# Cannot delete from PyPI, but can yank release
# Use PyPI web interface to "yank" problematic release

# Delete git tag if needed
git tag -d v0.2.0
git push origin :refs/tags/v0.2.0

# Revert commits if needed
git revert HEAD
```

## Release Checklist Template

Copy this checklist for each release:

### Pre-Release
- [ ] All tests pass
- [ ] Code formatted and linted
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in all files
- [ ] Dependencies reviewed

### Release
- [ ] Built distribution packages
- [ ] Tested locally
- [ ] Uploaded to TestPyPI
- [ ] Tested from TestPyPI
- [ ] Uploaded to PyPI
- [ ] Tested from PyPI

### Post-Release
- [ ] Git tag created and pushed
- [ ] GitHub release created
- [ ] Documentation updated
- [ ] Release announced

---

For more information, see the [Testing Guide](TESTING.md) or [main README](README.md).
