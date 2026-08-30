"""Shared fixtures: TestClient with both services overridden."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.integrations.cronometer import get_cronometer_service
from app.integrations.hevy import get_hevy_service


class FakeCronometer:
    def get_day_summary(self, day=None):
        return {"energy": 2180.0, "protein": 160.0, "carbs": 210.0, "fat": 72.0}


class FakeHevy:
    def last_workout(self):
        return {
            "date": "2026-08-30T09:10:55+00:00",
            "exercises": [
                {"name": "Lat Pulldown", "sets": [{"weight_kg": 55, "reps": 10}]}
            ],
        }


@pytest.fixture
def make_client():
    def _make():
        main.app.dependency_overrides[get_cronometer_service] = lambda: FakeCronometer()
        main.app.dependency_overrides[get_hevy_service] = lambda: FakeHevy()
        return TestClient(main.app)

    return _make
