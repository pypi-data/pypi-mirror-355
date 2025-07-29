#!/bin/bash
set -e

echo "Building and installing Smart MCP Proxy Python package system-wide..."

# Clean up previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "Building package..."
pip install build
python -m build

# Install the package system-wide using pip
echo "Installing package system-wide..."
pip install --user dist/*.whl --force-reinstall

# Add the user's Python bin directory to PATH if it's not already there
USER_BIN=$(python -m site --user-base)/bin
if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    echo "Adding $USER_BIN to PATH"
    echo 'export PATH="'$USER_BIN':$PATH"' >> ~/.zshrc
    echo "Please run 'source ~/.zshrc' to update your PATH"
fi

# Check if the command is available in the PATH
echo "Verifying installation..."
which smart-mcp-proxy || {
  echo "WARNING: smart-mcp-proxy command not found in PATH"
  echo "You may need to add $USER_BIN to your PATH manually"
  echo "You can add this line to your ~/.zshrc file:"
  echo 'export PATH="'$USER_BIN':$PATH"'
  exit 0
}

echo "Installation complete. You can now run 'smart-mcp-proxy' from any directory." 