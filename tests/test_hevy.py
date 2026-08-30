"""Tests for the Hevy integration service (httpx + respx, no real API)."""

import httpx
import respx

from app.integrations.hevy import HevyService


WORKOUT_PAYLOAD = {
    "workouts": [
        {
            "id": "w1",
            "start_time": "2026-08-30T09:10:55+00:00",
            "exercises": [
                {
                    "title": "Incline Bench Press (Dumbbell)",
                    "sets": [
                        {"weight_kg": 40, "reps": 9},
                        {"weight_kg": 40, "reps": 8},
                    ],
                },
                {
                    "title": "Lat Pulldown",
                    "sets": [{"weight_kg": 55, "reps": 10}],
                },
            ],
        }
    ]
}


@respx.mock
def test_last_workout_maps_latest_session():
    respx.get("https://api.hevyapp.com/v1/workouts").mock(
        return_value=httpx.Response(200, json=WORKOUT_PAYLOAD)
    )

    service = HevyService(api_key="test-key")
    workout = service.last_workout()

    assert workout["date"] == "2026-08-30T09:10:55+00:00"
    assert workout["exercises"][0]["name"] == "Incline Bench Press (Dumbbell)"
    assert workout["exercises"][0]["sets"] == [
        {"weight_kg": 40, "reps": 9},
        {"weight_kg": 40, "reps": 8},
    ]
    assert workout["exercises"][1]["name"] == "Lat Pulldown"


@respx.mock
def test_last_workout_sends_api_key_header():
    route = respx.get("https://api.hevyapp.com/v1/workouts").mock(
        return_value=httpx.Response(200, json=WORKOUT_PAYLOAD)
    )

    HevyService(api_key="test-key").last_workout()

    assert route.calls.last.request.headers["api-key"] == "test-key"
