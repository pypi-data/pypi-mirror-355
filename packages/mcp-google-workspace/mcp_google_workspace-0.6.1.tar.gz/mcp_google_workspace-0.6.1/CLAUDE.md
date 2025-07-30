# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the mcp-google-workspace MCP server (formerly mcp-gsuite) that provides integration with Google Workspace (Gmail and Google Calendar). It enables AI assistants to interact with Google services through the Model Context Protocol.

Note: This is a fork of the original mcp-gsuite with fixes for JSON Schema compatibility (updated to draft 2020-12) and deployment via PyPI instead of Smithery.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the server locally
uv run mcp-google-workspace

# Run with custom configuration
uv run mcp-google-workspace --gauth-file /path/to/.gauth.json \
                            --accounts-file /path/to/.accounts.json \
                            --credentials-dir /path/to/credentials

# Build package
uv build  # or ./deploy.sh

# Deploy to PyPI
uv publish --config-file .pypirc

# Debug with MCP Inspector
npx @modelcontextprotocol/inspector uv --directory /path/to/google-mcp run mcp-google-workspace

# Monitor logs (macOS)
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-google-workspace.log
```

## Architecture

The server follows a tool-based architecture:

1. **Entry Points**: `__init__.py` → `server.py` → tool handlers
2. **Authentication**: OAuth2 flow managed by `gauth.py`, stores tokens as `.oauth.{email}.json`
3. **Services**: `gmail.py` and `calendar.py` wrap Google API clients
4. **Tools**: Inherit from `ToolHandler` base class, implement specific operations
5. **Multi-account**: Each tool accepts a `user_id` parameter to select the account

Key architectural decisions:
- Tools are stateless - authentication happens per-request
- HTML email content is parsed with BeautifulSoup
- Attachments are downloaded to temp files
- All dates use ISO 8601 format in UTC

## Important Implementation Notes

When modifying Gmail tools:
- Email body extraction handles both plain text and HTML parts
- The `get_body()` function in `gmail.py` processes multipart messages
- Attachment handling creates temp files that must be cleaned up

When modifying Calendar tools:
- Events use RFC3339 datetime format
- Timezone handling is critical - use pytz for conversions
- Recurring events are not fully supported

Authentication flow:
- First use triggers browser OAuth consent
- Tokens auto-refresh using refresh_token
- Credentials stored in configurable directory

## Testing

Currently no automated tests exist. Test changes by:
1. Using MCP Inspector to verify tool responses
2. Testing with Claude Desktop integration
3. Monitoring server logs for errors