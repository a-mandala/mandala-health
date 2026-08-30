"""Tests for the US-1 quick-log UI on the dashboard and the HTMX flow."""

from fastapi.testclient import TestClient

from tests.test_api_food_log import SearchAndLogCronometer, make_cronometer_client


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


def test_log_htmx_request_returns_updated_macros_fragment():
    client, _ = make_cronometer_client()

    response = client.post(
        "/api/log",
        json={"food_id": 101, "measure_id": 10, "grams": 120.0, "meal": "lunch"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    html = response.text
    assert 'id="macros-summary"' in html
    assert "100" in html  # updated energy value from the fake service
    assert "<html" not in html.lower()  # fragment, not full page


def test_search_htmx_request_returns_dropdown_fragment():
    client, _ = make_cronometer_client()

    response = client.get(
        "/api/foods/search",
        params={"q": "banana"},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 200
    html = response.text
    assert "Banana" in html
    assert "89" in html  # kcal_per_100g visible next to the result
    assert "89.0 kcal/100g" in html


def test_ui_is_mobile_first_no_hover_only_controls(make_client):
    response = make_client().get("/")

    html = response.text
    assert 'name="viewport"' in html
    assert 'content="width=device-width, initial-scale=1"' in html
    # touch-friendly tap targets on search results and meal buttons
    assert "min-h-[44px]" in html
    # no hover-only interactive styling (mobile-first: no hover: prefixes)
    assert "hover:" not in html
