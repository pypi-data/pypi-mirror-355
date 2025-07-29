#!/bin/bash
# Simple test runner for voice-mcp

set -e

echo "🧪 Running voice-mcp tests..."

# Check if in python-package directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must run from python-package directory"
    exit 1
fi

# Install test dependencies if needed
echo "📦 Installing test dependencies..."
pip install -e ".[test]" --quiet

# Run tests with coverage
echo "🏃 Running tests..."
pytest -v --cov=src/voice_mcp --cov-report=term-missing

echo "✅ Tests complete!"