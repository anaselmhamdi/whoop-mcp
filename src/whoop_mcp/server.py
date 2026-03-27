from __future__ import annotations

import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, OAuthProxy
from fastmcp.server.dependencies import get_access_token

from whoop_mcp.auth import WHOOP_SCOPES, WhoopTokenVerifier
from whoop_mcp.client import WhoopClient

load_dotenv()

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


def _build_auth() -> OAuthProxy | None:
    """Build OAuthProxy if running in HTTP mode with credentials."""
    base_url = os.environ.get("BASE_URL")
    client_id = os.environ.get("WHOOP_CLIENT_ID")
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET")

    if not all([base_url, client_id, client_secret]):
        return None

    return OAuthProxy(
        upstream_authorization_endpoint=WHOOP_AUTH_URL,
        upstream_token_endpoint=WHOOP_TOKEN_URL,
        upstream_client_id=client_id,
        upstream_client_secret=client_secret,
        token_verifier=WhoopTokenVerifier(),
        base_url=base_url,
        valid_scopes=WHOOP_SCOPES,
        forward_pkce=False,
    )


mcp = FastMCP("whoop-mcp", auth=_build_auth())


def _get_access_token() -> str:
    """Get the WHOOP access token from auth context or env var."""
    token = get_access_token()
    if token is not None:
        return token.token

    # Fallback for local stdio mode
    access_token = os.environ.get("WHOOP_ACCESS_TOKEN", "")
    if not access_token:
        raise RuntimeError("Not authenticated.")
    return access_token


# ── User ─────────────────────────────────────────────────────────────────


@mcp.tool
async def get_profile() -> dict:
    """Get the authenticated user's WHOOP profile (name, email)."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get("/v1/user/profile/basic")


@mcp.tool
async def get_body_measurement() -> dict:
    """Get the user's body measurements (height, weight, max heart rate)."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get("/v1/user/measurement/body")


# ── Cycles ───────────────────────────────────────────────────────────────


@mcp.tool
async def get_cycles(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """List physiological cycles. Each cycle contains strain, kilojoules, and heart rate data.

    Args:
        start: ISO-8601 datetime to filter from (e.g. 2024-01-01T00:00:00.000Z).
        end: ISO-8601 datetime to filter until.
        limit: Max number of records to return (default fetches all pages).
    """
    params = _build_list_params(start, end, limit)
    async with WhoopClient(_get_access_token()) as client:
        if limit is not None:
            return (await client.get("/v1/cycle", params)).get("records", [])
        return await client.get_paginated("/v1/cycle", params)


@mcp.tool
async def get_cycle_by_id(cycle_id: str) -> dict:
    """Get a single physiological cycle by its ID."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get(f"/v1/cycle/{cycle_id}")


# ── Recovery ─────────────────────────────────────────────────────────────


@mcp.tool
async def get_recovery_collection(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """List recovery scores. Each record contains recovery %, HRV, resting heart rate, and SpO2.

    Args:
        start: ISO-8601 datetime to filter from.
        end: ISO-8601 datetime to filter until.
        limit: Max number of records to return (default fetches all pages).
    """
    params = _build_list_params(start, end, limit)
    async with WhoopClient(_get_access_token()) as client:
        if limit is not None:
            return (await client.get("/v1/recovery", params)).get("records", [])
        return await client.get_paginated("/v1/recovery", params)


@mcp.tool
async def get_recovery_by_id(cycle_id: str) -> dict:
    """Get a single recovery record by its associated cycle ID."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get(f"/v1/recovery/{cycle_id}")


# ── Sleep ────────────────────────────────────────────────────────────────


@mcp.tool
async def get_sleep_collection(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """List sleep records. Each record contains sleep stages, performance %, respiratory rate, and sleep needed.

    Args:
        start: ISO-8601 datetime to filter from.
        end: ISO-8601 datetime to filter until.
        limit: Max number of records to return (default fetches all pages).
    """
    params = _build_list_params(start, end, limit)
    async with WhoopClient(_get_access_token()) as client:
        if limit is not None:
            return (await client.get("/v1/sleep", params)).get("records", [])
        return await client.get_paginated("/v1/sleep", params)


@mcp.tool
async def get_sleep_by_id(sleep_id: str) -> dict:
    """Get a single sleep record by its ID."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get(f"/v1/sleep/{sleep_id}")


# ── Workouts ─────────────────────────────────────────────────────────────


@mcp.tool
async def get_workout_collection(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """List workouts. Each record contains sport type, strain, heart rate zones, distance, and altitude.

    Args:
        start: ISO-8601 datetime to filter from.
        end: ISO-8601 datetime to filter until.
        limit: Max number of records to return (default fetches all pages).
    """
    params = _build_list_params(start, end, limit)
    async with WhoopClient(_get_access_token()) as client:
        if limit is not None:
            return (await client.get("/v1/workout", params)).get("records", [])
        return await client.get_paginated("/v1/workout", params)


@mcp.tool
async def get_workout_by_id(workout_id: str) -> dict:
    """Get a single workout by its ID."""
    async with WhoopClient(_get_access_token()) as client:
        return await client.get(f"/v1/workout/{workout_id}")


# ── Helpers ──────────────────────────────────────────────────────────────


def _build_list_params(
    start: str | None, end: str | None, limit: int | None
) -> dict:
    params: dict = {}
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end
    if limit is not None:
        params["limit"] = limit
    return params


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "http":
        mcp.run(
            transport="http",
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8080")),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
