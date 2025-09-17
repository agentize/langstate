#!/bin/bash

# Development setup script for langstate

set -e

echo "🔧 Setting up development environment for langstate"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run this script from the package root."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"

# Check if Python version is supported
if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "❌ Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
echo "📦 Installing package in development mode..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Run initial tests
echo "🧪 Running initial tests..."
python -m pytest --maxfail=1

# Run linting
echo "🔍 Running linting check..."
flake8 langstate/ --count --select=E9,F63,F7,F82 --show-source --statistics

echo "✅ Development environment setup complete!"
echo ""
echo "🎉 You can now start developing!"
echo ""
echo "Useful commands:"
echo "  • Activate virtual environment: source venv/bin/activate"
echo "  • Run tests: pytest"
echo "  • Run application: langstate dev"
echo "  • Run linting: flake8 langstate/"
echo "  • Run type checking: mypy langstate/"
echo "  • Format code: black langstate/"
echo ""
echo "📝 Don't forget to:"
echo "  • Update your name and email in pyproject.toml and setup.py"
echo "  • Update the repository URL in pyproject.toml"
echo "  • Add your PyPI API token to GitHub secrets for CI/CD"
