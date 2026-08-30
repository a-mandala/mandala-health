"""Tests for the API routes (TestClient + dependency override of services)."""

from app import main


def test_today_returns_nutrition_and_last_workout(make_client):
    response = make_client().get("/api/today")

    assert response.status_code == 200
    assert response.json() == {
        "nutrition": {"energy": 2180.0, "protein": 160.0, "carbs": 210.0, "fat": 72.0},
        "last_workout": {
            "date": "2026-08-30T09:10:55+00:00",
            "exercises": [{"name": "Lat Pulldown", "sets": [{"weight_kg": 55, "reps": 10}]}],
        },
    }
