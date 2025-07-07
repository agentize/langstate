#!/bin/bash

# Production runner script for the sample app

set -e

echo "🚀 Starting Khandhas Sample App in Production Mode"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the sample-app directory."
    exit 1
fi

# Set production mode
export KHANDHAS_DEV_MODE=false

# Load environment variables from .env.prod file
if [ -f ".env.prod" ]; then
    echo "📝 Loading production environment variables from .env.prod"
    export $(cat .env.prod | xargs)
fi

# Check if the package is installed
if ! python -c "import khandhas" 2>/dev/null; then
    echo "❌ khandhas not found. Please install it first:"
    echo "   pip install khandhas"
    echo "   Or for development: pip install -e ../packages/python-lib"
    exit 1
fi

# Run the application
echo "🚀 Running in production mode..."
python main.py "$@"
