# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                    # Install dependencies
uv run pytest                              # Run all tests
uv run pytest tests/test_client.py -v      # Run a single test file
uv run pytest -k test_pagination -v        # Run a single test by name
uv run whoop-mcp                           # Run the MCP server (stdio)
uv run fastmcp dev src/whoop_mcp/server.py # Run with MCP Inspector
fly deploy                                 # Deploy to Fly.io
```

## Architecture

FastMCP server exposing the WHOOP v2 API as MCP tools. Three core files:

- **`src/whoop_mcp/client.py`** — `WhoopClient` wraps `httpx.AsyncClient` with pagination and rate limit handling. Used as an async context manager, one instance per tool call.

- **`src/whoop_mcp/auth.py`** — `WhoopTokenVerifier` validates opaque WHOOP tokens by calling the profile endpoint. Used by `OAuthProxy` to verify upstream tokens.

- **`src/whoop_mcp/server.py`** — Defines 10 MCP tools (1:1 with WHOOP endpoints). When deployed with `BASE_URL` set, uses FastMCP `OAuthProxy` for automatic OAuth flow. Falls back to `WHOOP_ACCESS_TOKEN` env var for local stdio mode.

## Auth

Two modes:
- **Remote (HTTP)**: `OAuthProxy` handles the full OAuth flow — client connects, browser opens for WHOOP login, tokens are managed automatically.
- **Local (stdio)**: Reads `WHOOP_ACCESS_TOKEN` from env / `.env` file.

## Testing

Tests use `pytest-asyncio` (auto mode) and `respx` for HTTP mocking.

- **`test_client.py`** — Tests `WhoopClient` with `respx` mocks.
- **`test_server.py`** — Patches `_get_access_token()` and `WhoopClient` to test tools in isolation.

Sample response data lives in `tests/conftest.py` as module-level constants.
