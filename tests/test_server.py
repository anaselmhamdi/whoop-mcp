from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from .conftest import (
    SAMPLE_BODY_MEASUREMENT,
    SAMPLE_CYCLE,
    SAMPLE_PROFILE,
    SAMPLE_RECOVERY,
    SAMPLE_SLEEP,
    SAMPLE_WORKOUT,
)


@pytest.fixture(autouse=True)
def mock_access_token():
    """Make _get_access_token return a test token for all tool tests."""
    with patch("whoop_mcp.server._get_access_token", return_value="test_token"):
        yield


@pytest.fixture
def mock_client():
    """Patch WhoopClient to return a mock."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("whoop_mcp.server.WhoopClient", return_value=client):
        yield client


# ── Profile & Body ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile(mock_client):
    mock_client.get.return_value = SAMPLE_PROFILE

    from whoop_mcp.server import get_profile

    result = await get_profile()
    assert result == SAMPLE_PROFILE
    mock_client.get.assert_called_once_with("/v1/user/profile/basic")


@pytest.mark.asyncio
async def test_get_body_measurement(mock_client):
    mock_client.get.return_value = SAMPLE_BODY_MEASUREMENT

    from whoop_mcp.server import get_body_measurement

    result = await get_body_measurement()
    assert result == SAMPLE_BODY_MEASUREMENT
    mock_client.get.assert_called_once_with("/v1/user/measurement/body")


# ── Cycles ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_cycles_paginated(mock_client):
    mock_client.get_paginated.return_value = [SAMPLE_CYCLE, SAMPLE_CYCLE]

    from whoop_mcp.server import get_cycles

    result = await get_cycles()
    assert len(result) == 2
    mock_client.get_paginated.assert_called_once_with("/v1/cycle", {})


@pytest.mark.asyncio
async def test_get_cycles_with_limit(mock_client):
    mock_client.get.return_value = {"records": [SAMPLE_CYCLE]}

    from whoop_mcp.server import get_cycles

    result = await get_cycles(start="2024-01-01T00:00:00.000Z", limit=5)
    assert result == [SAMPLE_CYCLE]
    mock_client.get.assert_called_once_with(
        "/v1/cycle", {"start": "2024-01-01T00:00:00.000Z", "limit": 5}
    )


@pytest.mark.asyncio
async def test_get_cycle_by_id(mock_client):
    mock_client.get.return_value = SAMPLE_CYCLE

    from whoop_mcp.server import get_cycle_by_id

    result = await get_cycle_by_id("abc-123")
    assert result == SAMPLE_CYCLE
    mock_client.get.assert_called_once_with("/v1/cycle/abc-123")


# ── Recovery ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_recovery_collection(mock_client):
    mock_client.get_paginated.return_value = [SAMPLE_RECOVERY]

    from whoop_mcp.server import get_recovery_collection

    result = await get_recovery_collection()
    assert result == [SAMPLE_RECOVERY]


@pytest.mark.asyncio
async def test_get_recovery_by_id(mock_client):
    mock_client.get.return_value = SAMPLE_RECOVERY

    from whoop_mcp.server import get_recovery_by_id

    result = await get_recovery_by_id("12345")
    assert result == SAMPLE_RECOVERY
    mock_client.get.assert_called_once_with("/v1/recovery/12345")


# ── Sleep ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_sleep_collection(mock_client):
    mock_client.get_paginated.return_value = [SAMPLE_SLEEP]

    from whoop_mcp.server import get_sleep_collection

    result = await get_sleep_collection()
    assert result == [SAMPLE_SLEEP]


@pytest.mark.asyncio
async def test_get_sleep_by_id(mock_client):
    mock_client.get.return_value = SAMPLE_SLEEP

    from whoop_mcp.server import get_sleep_by_id

    result = await get_sleep_by_id("sleep-abc")
    assert result == SAMPLE_SLEEP
    mock_client.get.assert_called_once_with("/v1/sleep/sleep-abc")


# ── Workouts ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_workout_collection(mock_client):
    mock_client.get_paginated.return_value = [SAMPLE_WORKOUT]

    from whoop_mcp.server import get_workout_collection

    result = await get_workout_collection()
    assert result == [SAMPLE_WORKOUT]


@pytest.mark.asyncio
async def test_get_workout_by_id(mock_client):
    mock_client.get.return_value = SAMPLE_WORKOUT

    from whoop_mcp.server import get_workout_by_id

    result = await get_workout_by_id("workout-abc")
    assert result == SAMPLE_WORKOUT
    mock_client.get.assert_called_once_with("/v1/workout/workout-abc")


# ── List tools with date filters ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_tool_passes_date_filters(mock_client):
    mock_client.get_paginated.return_value = []

    from whoop_mcp.server import get_sleep_collection

    await get_sleep_collection(start="2024-01-01T00:00:00.000Z", end="2024-02-01T00:00:00.000Z")
    mock_client.get_paginated.assert_called_once_with(
        "/v1/sleep",
        {"start": "2024-01-01T00:00:00.000Z", "end": "2024-02-01T00:00:00.000Z"},
    )
