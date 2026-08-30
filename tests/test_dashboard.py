"""Tests for the Jinja2 dashboard page (GET /)."""

from fastapi.testclient import TestClient


def test_dashboard_renders_targets_and_last_workout(make_client):
    response = make_client().get("/")

    assert response.status_code == 200
    html = response.text
    assert "178" in html           # kcal consumed (200 g banana)
    assert "2400" in html          # kcal target
    assert "155" in html           # protein target
    assert "Lat Pulldown" in html  # last workout card
