"""Tests for US-1 API endpoints against the real local FoodDatabase."""

import pytest


def test_food_search_endpoint_returns_results(make_client):
    client = make_client(log_banana=False)

    response = client.get("/api/foods/search", params={"q": "banana"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Banana"
    assert body[0]["kcal_per_100g"] == 89.0
    assert body[0]["protein_per_100g"] == 1.1
    assert body[0]["carbs_per_100g"] == 22.8
    assert body[0]["fat_per_100g"] == 0.3


def test_food_search_endpoint_requires_query(make_client):
    response = make_client().get("/api/foods/search")

    assert response.status_code == 422


def test_log_endpoint_persists_entry_and_returns_summary(make_client):
    client = make_client(log_banana=False)
    food_id = client.food_db.search("banana")[0]["food_id"]

    response = client.post(
        "/api/log",
        json={"food_id": food_id, "grams": 120.0, "meal": "lunch"},
    )

    assert response.status_code == 200
    # 89 kcal/100g * 120g = 106.8 kcal
    assert response.json()["nutrition"]["energy"] == pytest.approx(106.8)
    # entry is persisted in the DB with today's date
    assert client.food_db.day_summary()["energy"] == pytest.approx(106.8)


def test_log_endpoint_rejects_invalid_meal(make_client):
    client = make_client()
    food_id = client.food_db.search("banana")[0]["food_id"]

    response = client.post(
        "/api/log",
        json={"food_id": food_id, "grams": 120.0, "meal": "brunch"},
    )

    assert response.status_code == 422


def test_log_endpoint_rejects_non_positive_grams(make_client):
    client = make_client()
    food_id = client.food_db.search("banana")[0]["food_id"]

    response = client.post(
        "/api/log",
        json={"food_id": food_id, "grams": 0, "meal": "lunch"},
    )

    assert response.status_code == 422
