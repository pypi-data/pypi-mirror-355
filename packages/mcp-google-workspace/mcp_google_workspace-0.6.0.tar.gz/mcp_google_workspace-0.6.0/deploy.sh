#!/bin/bash

# Build and deploy script for mcp-google-workspace

echo "Building mcp-google-workspace package..."

# Clean previous builds
rm -rf dist/

# Build the package
uv build

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build successful!"
echo ""
echo "To publish to PyPI, run:"
echo "  uv publish --config-file .pypirc"
echo ""
echo "Or if you want to test locally first:"
echo "  pip install dist/mcp_google_workspace-*.whl"