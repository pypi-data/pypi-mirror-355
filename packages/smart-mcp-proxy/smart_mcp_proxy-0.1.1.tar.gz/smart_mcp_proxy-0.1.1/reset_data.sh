#!/bin/bash

# Smart MCP Proxy Data Reset Script
# This script removes all persistent data files to reset the proxy state

echo "Smart MCP Proxy - Data Reset Script"
echo "==================================="

# Files to remove
FILES_TO_REMOVE=(
    "tools.faiss"
    "proxy.db"
)

# Remove known data files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing: $file"
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
echo "Alternative: Set SP_RESET_DATA=true environment variable for automatic reset." 