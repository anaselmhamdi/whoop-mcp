from __future__ import annotations

import httpx
import pytest
import respx

from whoop_mcp.client import (
    BASE_URL,
    WhoopAPIError,
    WhoopClient,
    WhoopRateLimitError,
)

from .conftest import SAMPLE_CYCLE


@pytest.mark.asyncio
async def test_get_sends_auth_header(whoop_client: WhoopClient):
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/v1/user/profile/basic").mock(
            return_value=httpx.Response(200, json={"user_id": 1})
        )
        result = await whoop_client.get("/v1/user/profile/basic")

    assert result == {"user_id": 1}
    assert route.called
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer test_access_token"


@pytest.mark.asyncio
async def test_get_forwards_params(whoop_client: WhoopClient):
    with respx.mock(base_url=BASE_URL) as mock:
        route = mock.get("/v1/cycle").mock(
            return_value=httpx.Response(200, json={"records": []})
        )
        await whoop_client.get("/v1/cycle", {"start": "2024-01-01", "limit": "5"})

    request = route.calls[0].request
    assert "start=2024-01-01" in str(request.url)
    assert "limit=5" in str(request.url)


@pytest.mark.asyncio
async def test_pagination_combines_records(whoop_client: WhoopClient):
    page1 = {"records": [SAMPLE_CYCLE], "next_token": "page2"}
    page2 = {"records": [SAMPLE_CYCLE], "next_token": None}

    call_count = 0

    def side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/v1/cycle").mock(side_effect=side_effect)
        records = await whoop_client.get_paginated("/v1/cycle")

    assert len(records) == 2
    assert call_count == 2


@pytest.mark.asyncio
async def test_rate_limit_raises_error(whoop_client: WhoopClient):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/v1/cycle").mock(
            return_value=httpx.Response(
                429,
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "42",
                },
            )
        )
        with pytest.raises(WhoopRateLimitError, match="Rate limit exceeded"):
            await whoop_client.get("/v1/cycle")


@pytest.mark.asyncio
async def test_api_error_raises(whoop_client: WhoopClient):
    with respx.mock(base_url=BASE_URL) as mock:
        mock.get("/v1/cycle").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(WhoopAPIError, match="500"):
            await whoop_client.get("/v1/cycle")


@pytest.mark.asyncio
async def test_context_manager():
    async with WhoopClient("token") as client:
        assert client.access_token == "token"
