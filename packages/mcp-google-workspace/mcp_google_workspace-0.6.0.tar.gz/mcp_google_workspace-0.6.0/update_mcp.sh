#!/bin/bash
# Update script for mcp-google-workspace

echo "🔄 Updating mcp-google-workspace..."

# Update the MCP server
claude mcp update mcp-google-workspace

# Restart Claude
echo "🔄 Restarting Claude Desktop..."
claude restart

echo "✅ Update complete!"