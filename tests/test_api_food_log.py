"""Tests for the food endpoints: search + barcode via Open Food Facts."""

import pytest


def test_food_search_returns_off_results(make_client):
    response = make_client(log_banana=False).get("/api/foods/search", params={"q": "nutella"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0] == {
        "food_id": "3017620422003",
        "name": "Nutella",
        "brand": "Ferrero",
        "barcode": "3017620422003",
        "kcal_per_100g": 539.0,
        "protein_per_100g": 6.3,
        "carbs_per_100g": 57.5,
        "fat_per_100g": 30.9,
    }


def test_food_search_requires_query(make_client):
    response = make_client().get("/api/foods/search")

    assert response.status_code == 422


def test_food_search_off_unreachable_returns_clean_json_503(make_client):
    client = make_client()
    client.off.fail = True

    response = client.get("/api/foods/search", params={"q": "banana"})

    assert response.status_code == 503
    body = response.json()
    assert "detail" in body
    assert "open food facts" in body["detail"].lower()


def test_barcode_endpoint_returns_normalized_product(make_client):
    response = make_client().get("/api/foods/barcode/9001")

    assert response.status_code == 200
    body = response.json()
    assert body["food_id"] == "9001"
    assert body["name"] == "Banana"
    assert body["kcal_per_100g"] == 89.0


def test_barcode_endpoint_unknown_product_returns_404(make_client):
    response = make_client().get("/api/foods/barcode/0000")

    assert response.status_code == 404


def test_barcode_endpoint_off_unreachable_returns_503(make_client):
    client = make_client()
    client.off.fail = True

    response = client.get("/api/foods/barcode/9001")

    assert response.status_code == 503
