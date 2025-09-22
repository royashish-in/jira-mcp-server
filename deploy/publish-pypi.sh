#!/bin/bash
set -e

# Change to project root directory
cd "$(dirname "$0")/.."

echo "Building package with uv..."
uv build

echo "Checking package..."
uv run twine check dist/*

echo "Uploading to PyPI..."
uv run twine upload --verbose dist/*

echo "Package published successfully!"
echo "Install with: pip install jira-mcp-server"