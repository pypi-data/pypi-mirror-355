#!/bin/bash
set -e
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info
echo "🔨 Building package..."
uv run python -m build
echo "✅ Checking package..."
uv run twine check dist/*
uv run twine upload dist/*
echo "✅ Deployment complete!"
