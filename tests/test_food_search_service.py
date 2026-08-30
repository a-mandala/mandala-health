"""Tests for CronometerService.search_foods (US-1 food search)."""

from app.integrations.cronometer import CronometerService


class FakeCronometerClient:
    def search_food(self, query):
        assert isinstance(query, str)
        return [
            {
                "id": 101,
                "name": "Banana",
                "measureId": 10,
                "measureDisplayName": "g",
                "source": "CRDB",
            },
            {
                "id": 102,
                "name": "Bran cereal",
                "measureId": 20,
                "measureDisplayName": "cup",
                "source": "NCCDB",
            },
        ]

    def get_foods(self, food_ids):
        assert food_ids == [101, 102]
        return [
            {
                "id": 101,
                "name": "Banana",
                "source": "CRDB",
                "nutrients": {"energy": 89.0, "protein": 1.1},
            },
            {
                "id": 102,
                "name": "Bran cereal",
                "source": "NCCDB",
                "nutrients": {"energy": 320.0, "protein": 9.0},
            },
        ]


def test_search_foods_returns_normalized_results_with_per_100g_macros():
    service = CronometerService(client=FakeCronometerClient())

    results = service.search_foods("bran")

    assert results == [
        {
            "food_id": 101,
            "measure_id": 10,
            "name": "Banana",
            "source": "CRDB",
            "measure_display": "g",
            "kcal_per_100g": 89.0,
            "protein_per_100g": 1.1,
        },
        {
            "food_id": 102,
            "measure_id": 20,
            "name": "Bran cereal",
            "source": "NCCDB",
            "measure_display": "cup",
            "kcal_per_100g": 320.0,
            "protein_per_100g": 9.0,
        },
    ]


def test_search_foods_handles_food_without_energy():
    class NoEnergyClient(FakeCronometerClient):
        def get_foods(self, food_ids):
            return [
                {
                    "id": 101,
                    "nutrients": {},
                }
            ]

    service = CronometerService(client=NoEnergyClient())

    results = service.search_foods("banana")

    assert results[0]["kcal_per_100g"] is None
    assert results[0]["protein_per_100g"] is None
