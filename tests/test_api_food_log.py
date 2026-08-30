"""Tests for US-1 API endpoints: GET /api/foods/search and POST /api/log."""

from fastapi.testclient import TestClient

from app.integrations.cronometer import get_cronometer_service


class SearchAndLogCronometer:
    def get_day_summary(self, day=None):
        return {"energy": 100.0, "protein": 10.0, "carbs": 5.0, "fat": 2.0}

    def search_foods(self, query):
        assert query == "banana"
        return [
            {
                "food_id": 101,
                "measure_id": 10,
                "name": "Banana",
                "source": "CRDB",
                "measure_display": "g",
                "kcal_per_100g": 89.0,
                "protein_per_100g": 1.1,
            }
        ]

    def add_food_entry(self, food_id, measure_id, grams, meal):
        self.last_call = {
            "food_id": food_id,
            "measure_id": measure_id,
            "grams": grams,
            "meal": meal,
        }
        return {"id": "srv-1"}


def make_cronometer_client(service=None):
    service = service or SearchAndLogCronometer()
    from app import main

    main.app.dependency_overrides[get_cronometer_service] = lambda: service
    return TestClient(main.app), service


def test_food_search_endpoint_returns_results():
    client, _ = make_cronometer_client()

    response = client.get("/api/foods/search", params={"q": "banana"})

    assert response.status_code == 200
    body = response.json()
    assert body == [
        {
            "food_id": 101,
            "measure_id": 10,
            "name": "Banana",
            "source": "CRDB",
            "measure_display": "g",
            "kcal_per_100g": 89.0,
            "protein_per_100g": 1.1,
        }
    ]


def test_food_search_endpoint_requires_query():
    client, _ = make_cronometer_client()

    response = client.get("/api/foods/search")

    assert response.status_code == 422


def test_log_endpoint_calls_add_food_entry_and_returns_summary():
    client, service = make_cronometer_client()

    response = client.post(
        "/api/log",
        json={"food_id": 101, "measure_id": 10, "grams": 120.0, "meal": "lunch"},
    )

    assert response.status_code == 200
    assert service.last_call == {
        "food_id": 101,
        "measure_id": 10,
        "grams": 120.0,
        "meal": "lunch",
    }
    body = response.json()
    assert body["nutrition"] == {
        "energy": 100.0,
        "protein": 10.0,
        "carbs": 5.0,
        "fat": 2.0,
    }


def test_log_endpoint_rejects_invalid_meal():
    client, _ = make_cronometer_client()

    response = client.post(
        "/api/log",
        json={"food_id": 101, "measure_id": 10, "grams": 120.0, "meal": "brunch"},
    )

    assert response.status_code == 422
