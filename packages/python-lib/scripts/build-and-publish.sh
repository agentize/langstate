#!/bin/bash

# Build and publish script for khandhas

set -e

echo "🚀 Starting build and publish process for khandhas"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run this script from the package root."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ There are uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Get the current version
VERSION=$(python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])")
echo "📦 Current version: $VERSION"

# Check if this version already exists on PyPI
if pip index versions khandhas 2>/dev/null | grep -q "$VERSION"; then
    echo "❌ Version $VERSION already exists on PyPI"
    exit 1
fi

# Install build dependencies
echo "🔧 Installing build dependencies..."
pip install --upgrade pip build twine

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Run tests
echo "🧪 Running tests..."
python -m pytest

# Run linting
echo "🔍 Running linting..."
flake8 khandhas/

# Run type checking
echo "🔍 Running type checking..."
mypy khandhas/

# Build the package
echo "📦 Building package..."
python -m build

# Check the package
echo "🔍 Checking package..."
twine check dist/*

# Upload to PyPI
echo "🚀 Uploading to PyPI..."
if [ "$1" = "--test" ]; then
    echo "📤 Uploading to Test PyPI..."
    twine upload --repository testpypi dist/*
else
    echo "📤 Uploading to PyPI..."
    twine upload dist/*
fi

# Create git tag
echo "🏷️  Creating git tag..."
git tag "v$VERSION"
git push origin "v$VERSION"

echo "✅ Package published successfully!"
echo "🎉 Version $VERSION is now available on PyPI"
