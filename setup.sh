#!/bin/bash
# Quick setup script for Khandhas development environment

set -e  # Exit on any error

echo "🚀 Setting up Khandhas development environment..."

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.9+ first."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "🐍 Using Python: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
else
    echo "📦 Virtual environment already exists"
fi

# Determine activation script based on OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    ACTIVATE_SCRIPT=".venv/Scripts/activate"
    PYTHON_PATH=".venv/Scripts/python"
else
    ACTIVATE_SCRIPT=".venv/bin/activate"
    PYTHON_PATH=".venv/bin/python"
fi

# Activate virtual environment and install dependencies
echo "⚙️  Installing dependencies..."
source $ACTIVATE_SCRIPT

# Upgrade pip
$PYTHON_PATH -m pip install --upgrade pip

# Install the package in development mode
cd packages/python-lib
$PYTHON_PATH -m pip install -e ".[dev]"
cd ../..

# Verify installation
echo "🔍 Verifying installation..."
$PYTHON_PATH -c "import khandhas; print(f'✅ Khandhas {khandhas.__version__} installed successfully')"

# Run a quick test
echo "🧪 Running quick test..."
cd packages/python-lib
$PYTHON_PATH -m pytest tests/ -q --tb=no
cd ../..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To activate the virtual environment:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "  .venv\\Scripts\\activate"
else
    echo "  source .venv/bin/activate"
fi
echo ""
echo "To try the sample app:"
echo "  cd sample-app"
echo "  python main.py"
echo ""
echo "To run tests:"
echo "  cd packages/python-lib"
echo "  pytest"
echo ""
echo "To verify everything works:"
echo "  python packages/python-lib/verify.py"
