"""Tests for the API routes (TestClient + dependency override of services)."""

import pytest


def test_today_returns_nutrition_and_last_workout(make_client):
    response = make_client().get("/api/today")

    assert response.status_code == 200
    body = response.json()
    # 200 g of seeded banana (89 kcal/100g) logged at breakfast
    assert body["nutrition"]["energy"] == pytest.approx(178.0)
    assert body["nutrition"]["protein"] == pytest.approx(2.2)
    assert body["last_workout"] == {
        "date": "2026-08-30T09:10:55+00:00",
        "exercises": [{"name": "Lat Pulldown", "sets": [{"weight_kg": 55, "reps": 10}]}],
    }
