from __future__ import annotations

import os
import urllib.parse

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from whoop_mcp.client import TOKEN_URL, WhoopClient

load_dotenv()

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_SCOPES = "read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout offline"

mcp = FastMCP("whoop-mcp")

_client: WhoopClient | None = None


def _get_client() -> WhoopClient:
    global _client
    if _client is None:
        access_token = os.environ.get("WHOOP_ACCESS_TOKEN", "")
        refresh_token = os.environ.get("WHOOP_REFRESH_TOKEN", "")
        if not access_token or access_token == "your_access_token":
            raise RuntimeError("Not authenticated. Visit /login to connect your WHOOP account.")
        _client = WhoopClient(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=os.environ["WHOOP_CLIENT_ID"],
            client_secret=os.environ["WHOOP_CLIENT_SECRET"],
        )
    return _client


def _get_base_url() -> str:
    return os.environ.get("BASE_URL", "http://localhost:8080")


# ── OAuth routes ─────────────────────────────────────────────────────────


@mcp.custom_route("/login", methods=["GET"])
async def login(request: Request):
    callback_url = f"{_get_base_url()}/callback"
    params = urllib.parse.urlencode({
        "client_id": os.environ["WHOOP_CLIENT_ID"],
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": WHOOP_SCOPES,
        "state": "whoopauth1",
    })
    return RedirectResponse(f"{WHOOP_AUTH_URL}?{params}")


@mcp.custom_route("/callback", methods=["GET"])
async def callback(request: Request):
    global _client

    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(f"<h1>Auth failed</h1><p>{error}: {request.query_params.get('error_description', '')}</p>", status_code=400)

    if not code:
        return HTMLResponse("<h1>Missing authorization code</h1>", status_code=400)

    callback_url = f"{_get_base_url()}/callback"
    async with httpx.AsyncClient() as http:
        response = await http.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": os.environ["WHOOP_CLIENT_ID"],
                "client_secret": os.environ["WHOOP_CLIENT_SECRET"],
                "redirect_uri": callback_url,
            },
        )

    if response.status_code != 200:
        return HTMLResponse(f"<h1>Token exchange failed</h1><pre>{response.text}</pre>", status_code=400)

    body = response.json()

    _client = WhoopClient(
        access_token=body["access_token"],
        refresh_token=body.get("refresh_token", ""),
        client_id=os.environ["WHOOP_CLIENT_ID"],
        client_secret=os.environ["WHOOP_CLIENT_SECRET"],
    )

    return HTMLResponse("<h1>Connected to WHOOP!</h1><p>You can close this tab. The MCP server is ready.</p>")


# ── User ─────────────────────────────────────────────────────────────────


@mcp.tool
async def get_profile() -> dict:
    """Get the authenticated user's WHOOP profile (name, email)."""
    return await _get_client().get("/v1/user/profile/basic")


@mcp.tool
async def get_body_measurement() -> dict:
    """Get the user's body measurements (height, weight, max heart rate)."""
    return await _get_client().get("/v1/user/measurement/body")


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
    client = _get_client()
    params = _build_list_params(start, end, limit)

    if limit is not None:
        return (await client.get("/v1/cycle", params)).get("records", [])
    return await client.get_paginated("/v1/cycle", params)


@mcp.tool
async def get_cycle_by_id(cycle_id: str) -> dict:
    """Get a single physiological cycle by its ID."""
    return await _get_client().get(f"/v1/cycle/{cycle_id}")


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
    client = _get_client()
    params = _build_list_params(start, end, limit)

    if limit is not None:
        return (await client.get("/v1/recovery", params)).get("records", [])
    return await client.get_paginated("/v1/recovery", params)


@mcp.tool
async def get_recovery_by_id(cycle_id: str) -> dict:
    """Get a single recovery record by its associated cycle ID."""
    return await _get_client().get(f"/v1/recovery/{cycle_id}")


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
    client = _get_client()
    params = _build_list_params(start, end, limit)

    if limit is not None:
        return (await client.get("/v1/sleep", params)).get("records", [])
    return await client.get_paginated("/v1/sleep", params)


@mcp.tool
async def get_sleep_by_id(sleep_id: str) -> dict:
    """Get a single sleep record by its ID."""
    return await _get_client().get(f"/v1/sleep/{sleep_id}")


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
    client = _get_client()
    params = _build_list_params(start, end, limit)

    if limit is not None:
        return (await client.get("/v1/workout", params)).get("records", [])
    return await client.get_paginated("/v1/workout", params)


@mcp.tool
async def get_workout_by_id(workout_id: str) -> dict:
    """Get a single workout by its ID."""
    return await _get_client().get(f"/v1/workout/{workout_id}")


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
