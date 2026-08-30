"""Tests for the quick-log UI on the dashboard and the HTMX flow."""

import pytest

BANANA_PAYLOAD = {
    "food_id": "9001",
    "name": "Banana",
    "kcal_per_100g": 89.0,
    "protein_per_100g": 1.1,
    "carbs_per_100g": 22.8,
    "fat_per_100g": 0.3,
}


def test_dashboard_has_quick_log_form(make_client):
    html = make_client().get("/").text

    assert 'id="food-search"' in html
    assert 'hx-get="/api/foods/search"' in html
    assert 'id="grams"' in html and 'inputmode="decimal"' in html
    for label in ("Colazione", "Pranzo", "Cena", "Snack"):
        assert label in html
    assert "Aggiungi" in html
    assert 'hx-post="/api/log"' in html


def test_dashboard_macros_section_is_htmx_target(make_client):
    html = make_client().get("/").text

    assert 'id="macros-summary"' in html


def test_log_endpoint_persists_snapshot_entry_and_returns_summary(make_client):
    from datetime import date

    client = make_client(log_banana=False)

    response = client.post("/api/log", json={**BANANA_PAYLOAD, "grams": 120.0, "meal": "lunch"})

    assert response.status_code == 200
    # 89 kcal/100g * 120g = 106.8 kcal
    assert response.json()["nutrition"]["energy"] == pytest.approx(106.8)
    # entry persisted locally with the food snapshot + today's date
    today = date.today().isoformat()
    rows = client.store.entries_for(today)
    assert len(rows) == 1
    assert rows[0]["food_code"] == "9001"
    assert rows[0]["name"] == "Banana"
    assert rows[0]["kcal_per_100g"] == 89.0
    assert rows[0]["grams"] == 120.0


def test_log_htmx_request_returns_updated_macros_fragment(make_client):
    client = make_client(log_banana=False)

    response = client.post(
        "/api/log",
        json={**BANANA_PAYLOAD, "grams": 120.0, "meal": "lunch"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    html = response.text
    assert 'id="macros-summary"' in html
    assert "107" in html  # 89 kcal/100g * 120 g (rounded in the fragment)
    assert "<html" not in html.lower()  # fragment, not full page


def test_log_endpoint_rejects_invalid_meal(make_client):
    response = make_client().post(
        "/api/log", json={**BANANA_PAYLOAD, "grams": 120.0, "meal": "brunch"}
    )

    assert response.status_code == 422


def test_log_endpoint_rejects_non_positive_grams(make_client):
    response = make_client().post(
        "/api/log", json={**BANANA_PAYLOAD, "grams": 0, "meal": "lunch"}
    )

    assert response.status_code == 422


def test_search_htmx_request_returns_dropdown_fragment(make_client):
    client = make_client(log_banana=False)

    response = client.get(
        "/api/foods/search",
        params={"q": "nutella"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    html = response.text
    assert "Nutella" in html
    assert "Ferrero" in html  # brand shown alongside name
    assert "539.0 kcal/100g" in html


def test_ui_is_mobile_first_no_hover_only_controls(make_client):
    response = make_client().get("/")

    html = response.text
    assert 'name="viewport"' in html
    assert 'content="width=device-width, initial-scale=1"' in html
    # touch-friendly tap targets on search results and meal buttons
    assert "min-h-[44px]" in html
    # no hover-only interactive styling (mobile-first: no hover: prefixes)
    assert "hover:" not in html
