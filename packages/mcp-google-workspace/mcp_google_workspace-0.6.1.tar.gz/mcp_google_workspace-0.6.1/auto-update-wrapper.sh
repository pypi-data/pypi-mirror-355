#!/bin/bash
# Auto-update wrapper for mcp-google-workspace

# Check for updates every 24 hours
CACHE_FILE="$HOME/.cache/mcp-google-workspace-last-check"
CURRENT_TIME=$(date +%s)

if [ -f "$CACHE_FILE" ]; then
    LAST_CHECK=$(cat "$CACHE_FILE")
    TIME_DIFF=$((CURRENT_TIME - LAST_CHECK))
    
    # 86400 seconds = 24 hours
    if [ $TIME_DIFF -gt 86400 ]; then
        echo "Checking for updates..." >&2
        uvx --refresh mcp-google-workspace@latest --version >&2
        echo "$CURRENT_TIME" > "$CACHE_FILE"
    fi
else
    echo "$CURRENT_TIME" > "$CACHE_FILE"
fi

# Run the actual server
exec uvx --refresh mcp-google-workspace@latest "$@"