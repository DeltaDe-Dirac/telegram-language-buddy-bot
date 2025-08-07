#!/usr/bin/env bash
# Custom Heroku build script

set -e  # Exit on any error

echo "=== Custom Heroku Build Script ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set test environment
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///:memory:

# Run tests
echo "Running tests..."
python -m pytest tests/ -v --tb=short

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed! Build successful."
    echo "Test coverage report:"
    python -m pytest tests/ --cov=src --cov-report=term-missing
    echo "Build completed successfully!"
    exit 0
else
    echo "❌ Tests failed! Build failed."
    echo "Please fix the failing tests before deploying."
    exit 1
fi
