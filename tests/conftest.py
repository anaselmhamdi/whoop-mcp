from __future__ import annotations

import pytest

from whoop_mcp.client import WhoopClient


SAMPLE_PROFILE = {
    "user_id": 12345,
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
}

SAMPLE_BODY_MEASUREMENT = {
    "height_meter": 1.75,
    "weight_kilogram": 70.0,
    "max_heart_rate": 195,
}

SAMPLE_CYCLE = {
    "id": "abc-123",
    "user_id": 12345,
    "start": "2024-01-15T00:00:00.000Z",
    "end": "2024-01-16T00:00:00.000Z",
    "score_state": "SCORED",
    "score": {
        "strain": 12.5,
        "kilojoule": 2100.0,
        "average_heart_rate": 72,
        "max_heart_rate": 185,
    },
}

SAMPLE_RECOVERY = {
    "cycle_id": 12345,
    "sleep_id": "sleep-abc",
    "user_id": 12345,
    "score_state": "SCORED",
    "score": {
        "user_calibrating": False,
        "recovery_score": 78.0,
        "resting_heart_rate": 55.0,
        "hrv_rmssd_milli": 45.2,
        "spo2_percentage": 97.0,
        "skin_temp_celsius": 33.5,
    },
}

SAMPLE_SLEEP = {
    "id": "sleep-abc",
    "user_id": 12345,
    "start": "2024-01-15T22:00:00.000Z",
    "end": "2024-01-16T06:30:00.000Z",
    "nap": False,
    "score_state": "SCORED",
    "score": {
        "stage_summary": {
            "total_in_bed_time_milli": 30600000,
            "total_light_sleep_time_milli": 14400000,
            "total_slow_wave_sleep_time_milli": 7200000,
            "total_rem_sleep_time_milli": 5400000,
            "total_awake_time_milli": 3600000,
        },
        "sleep_performance_percentage": 85.0,
        "respiratory_rate": 15.2,
    },
}

SAMPLE_WORKOUT = {
    "id": "workout-abc",
    "user_id": 12345,
    "start": "2024-01-15T07:00:00.000Z",
    "end": "2024-01-15T08:00:00.000Z",
    "sport_id": 1,
    "score_state": "SCORED",
    "score": {
        "strain": 14.2,
        "average_heart_rate": 145,
        "max_heart_rate": 180,
        "kilojoule": 1200.0,
        "distance_meter": 8500.0,
        "altitude_gain_meter": 50.0,
        "zone_duration": {},
    },
}


@pytest.fixture
def whoop_client():
    return WhoopClient(access_token="test_access_token")
