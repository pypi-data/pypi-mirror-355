#!/bin/bash

# Smart MCP Proxy Data Reset Script
# This script removes all persistent data files to reset the proxy state

echo "Smart MCP Proxy - Data Reset Script"
echo "==================================="

# Determine data directory
if [ -n "$MCPPROXY_DATA_DIR" ]; then
    DATA_DIR="$MCPPROXY_DATA_DIR"
    echo "Using MCPPROXY_DATA_DIR: $DATA_DIR"
else
    # Default data directory
    DATA_DIR="$HOME/.mcpproxy"
    if [ ! -d "$DATA_DIR" ]; then
        # Fallback to temp directory if home directory version doesn't exist
        DATA_DIR="/tmp/mcpproxy"
    fi
    echo "Using default data directory: $DATA_DIR"
fi

# Files to remove in data directory
FILES_TO_REMOVE=(
    "tools.faiss"
    "proxy.db"
)

# Remove known data files from data directory
if [ -d "$DATA_DIR" ]; then
    echo "Checking data directory: $DATA_DIR"
    for file in "${FILES_TO_REMOVE[@]}"; do
        filepath="$DATA_DIR/$file"
        if [ -f "$filepath" ]; then
            echo "Removing: $filepath"
            rm "$filepath"
        else
            echo "Not found: $filepath (skipping)"
        fi
    done
else
    echo "Data directory does not exist: $DATA_DIR"
fi

# Also check current directory for backward compatibility
echo "Checking current directory for legacy files..."
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing legacy file: $file"
        rm "$file"
    else
        echo "Not found: $file (skipping)"
    fi
done

# Remove BM25 index directories (temp directories starting with bm25s_)
echo "Looking for BM25 index directories..."
for dir in /tmp/bm25s_*; do
    if [ -d "$dir" ]; then
        echo "Removing BM25 index directory: $dir"
        rm -rf "$dir"
    fi
done

# Also check current directory for any bm25s_ directories
for dir in bm25s_*; do
    if [ -d "$dir" ]; then
        echo "Removing BM25 index directory: $dir"
        rm -rf "$dir"
    fi
done

echo ""
echo "Data reset complete!"
echo "You can now restart the Smart MCP Proxy."
echo ""
echo "Alternative: Set MCPPROXY_RESET_DATA=true environment variable for automatic reset."
echo ""
echo "Note: To specify a custom data directory, set MCPPROXY_DATA_DIR environment variable." 