"""Tests for CronometerService.add_food_entry (US-1 quick log)."""

import pytest

from app.integrations.cronometer import CronometerService


class RecordingClient:
    def __init__(self):
        self.calls = []

    def add_serving(self, *, food_id, measure_id, grams, diary_group, **kwargs):
        self.calls.append(
            {
                "food_id": food_id,
                "measure_id": measure_id,
                "grams": grams,
                "diary_group": diary_group,
            }
        )
        return {"id": "srv-1"}


@pytest.mark.parametrize(
    ("meal", "expected_group"),
    [("breakfast", 1), ("lunch", 2), ("dinner", 3), ("snacks", 4)],
)
def test_add_food_entry_maps_meal_name_to_diary_group(meal, expected_group):
    client = RecordingClient()
    service = CronometerService(client=client)

    result = service.add_food_entry(
        food_id=101, measure_id=10, grams=120.0, meal=meal
    )

    assert result == {"id": "srv-1"}
    assert client.calls == [
        {
            "food_id": 101,
            "measure_id": 10,
            "grams": 120.0,
            "diary_group": expected_group,
        }
    ]


def test_add_food_entry_rejects_unknown_meal():
    service = CronometerService(client=RecordingClient())

    with pytest.raises(ValueError):
        service.add_food_entry(food_id=1, measure_id=1, grams=10, meal="brunch")
