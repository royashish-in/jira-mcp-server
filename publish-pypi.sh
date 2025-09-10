#!/bin/bash
set -e

echo "Building package..."
python -m build

echo "Checking package..."
python -m twine check dist/*

echo "Uploading to PyPI..."
python -m twine upload dist/*

echo "Package published successfully!"
echo "Install with: pip install jira-mcp-server"