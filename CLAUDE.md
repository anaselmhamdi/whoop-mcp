# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                    # Install dependencies
uv run pytest                              # Run all tests
uv run pytest tests/test_client.py -v      # Run a single test file
uv run pytest -k test_auto_refresh -v      # Run a single test by name
uv run whoop-mcp                           # Run the MCP server
uv run fastmcp dev src/whoop_mcp/server.py # Run with MCP Inspector
uv run python scripts/refresh_token.py     # Manually refresh OAuth tokens
```

## Architecture

This is a FastMCP server exposing the WHOOP v2 API as MCP tools. Two core files:

- **`src/whoop_mcp/client.py`** — `WhoopClient` wraps `httpx.AsyncClient` with automatic OAuth token refresh on 401, `nextToken`-based pagination, and rate limit handling. Three custom exceptions: `WhoopAuthError`, `WhoopRateLimitError`, `WhoopAPIError`.

- **`src/whoop_mcp/server.py`** — Defines 10 MCP tools (1:1 with WHOOP endpoints) plus `/login` and `/callback` OAuth routes for browser-based auth. Uses a lazily-initialized global `WhoopClient` singleton. List tools accept optional `start`/`end`/`limit` params; when `limit` is set they return a single page, otherwise they auto-paginate. Supports both `stdio` (local) and `http` (remote) transport via `MCP_TRANSPORT` env var.

## Testing

Tests use `pytest-asyncio` (auto mode) and `respx` for HTTP mocking. Two test files:

- **`test_client.py`** — Tests against real `WhoopClient` with `respx` mocks. Uses dual mock contexts for API calls (`BASE_URL`) and token refresh (`TOKEN_URL`).
- **`test_server.py`** — Patches `_get_client()` with `AsyncMock` to test tool functions in isolation.

Sample response data lives in `tests/conftest.py` as module-level constants.

## Deployment

Deployed to Fly.io with auto-deploy via GitHub Actions on push to `main`. Config in `fly.toml`, workflow in `.github/workflows/deploy.yml`. The deployed server uses HTTP transport and exposes `/login` + `/callback` routes for OAuth.

## Environment

Requires `WHOOP_CLIENT_ID` and `WHOOP_CLIENT_SECRET` (always). `WHOOP_ACCESS_TOKEN` and `WHOOP_REFRESH_TOKEN` can be set via env or obtained through the `/login` OAuth flow. For remote deployment, also set `BASE_URL` and `MCP_TRANSPORT=http`.
