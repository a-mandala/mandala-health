"""Shared fixtures: TestClient with a real (tmp) FoodDatabase and fake Hevy."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.integrations.food_db import FoodDatabase, get_food_db_service
from app.integrations.hevy import get_hevy_service


class FakeHevy:
    def last_workout(self):
        return {
            "date": "2026-08-30T09:10:55+00:00",
            "exercises": [
                {"name": "Lat Pulldown", "sets": [{"weight_kg": 55, "reps": 10}]}
            ],
        }


@pytest.fixture
def make_client(tmp_path):
    """Fresh app client backed by a real SQLite FoodDatabase in tmp_path.

    Seeds one food (Banana, 89 kcal/100g) and optionally logs 200 g at
    breakfast (=> 178 kcal, 2.2 g protein). The client exposes `food_db`.
    """

    def _make(log_banana: bool = True):
        db = FoodDatabase(db_path=tmp_path / "foods.db")
        food_id = db.add_custom_food("Banana", 89.0, 1.1, 22.8, 0.3)
        if log_banana:
            db.log_entry(food_id, 200.0, "breakfast")
        main.app.dependency_overrides[get_food_db_service] = lambda: db
        main.app.dependency_overrides[get_hevy_service] = lambda: FakeHevy()
        client = TestClient(main.app)
        client.food_db = db
        return client

    return _make
