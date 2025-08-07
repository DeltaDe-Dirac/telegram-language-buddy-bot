#!/usr/bin/env bash
# Heroku build script - runs tests before deployment

echo "=== Running tests before deployment ==="

# Run all tests
python -m pytest tests/ -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed! Proceeding with deployment..."
    exit 0
else
    echo "❌ Tests failed! Deployment aborted."
    echo "Please fix the failing tests before deploying."
    exit 1
fi
