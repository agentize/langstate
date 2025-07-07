#!/bin/bash

# Development runner script for the sample app

set -e

echo "🚀 Starting Khandhas Sample App in Development Mode"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the sample-app directory."
    exit 1
fi

# Set development mode
export KHANDHAS_DEV_MODE=true

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | xargs)
fi

# Check if the package is installed in development mode
PACKAGE_PATH="../packages/python-lib"
if [ ! -d "$PACKAGE_PATH" ]; then
    echo "❌ Package path not found: $PACKAGE_PATH"
    exit 1
fi

# Install package in development mode if not already installed
if ! python -c "import khandhas" 2>/dev/null; then
    echo "📦 Installing khandhas in development mode..."
    cd "$PACKAGE_PATH"
    pip install -e .
    cd - > /dev/null
fi

# Run the application
echo "🔧 Running in development mode with live reloading..."
python main.py "$@"
