"""TDD tests for the Open Food Facts integration (respx-mocked, offline)."""

import httpx
import pytest
import respx

from app.integrations.off import OFFError, OFFService

BASE = "https://world.openfoodfacts.org"


def off_product(code="3017620422003", name="Nutella", brand="Ferrero"):
    """Minimal OFF v2 product shape with all fields present."""
    return {
        "code": code,
        "product_name": name,
        "brands": brand,
        "nutriments": {
            "energy-kcal_100g": 539.0,
            "proteins_100g": 6.3,
            "carbohydrates_100g": 57.5,
            "fat_100g": 30.9,
        },
        "completeness": 0.8,
    }


def off_search_response(products):
    return {"count": len(products), "products": products}


@respx.mock
def test_search_normalizes_off_products():
    respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([off_product()]))
    )
    svc = OFFService()

    results = svc.search("nutella")

    assert results == [
        {
            "food_id": "3017620422003",
            "name": "Nutella",
            "brand": "Ferrero",
            "barcode": "3017620422003",
            "kcal_per_100g": 539.0,
            "protein_per_100g": 6.3,
            "carbs_per_100g": 57.5,
            "fat_per_100g": 30.9,
        }
    ]


@respx.mock
def test_search_sends_query_and_page_size_params():
    route = respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([]))
    )
    svc = OFFService()

    svc.search("banana")

    params = route.calls.last.request.url.params
    assert params["search_terms"] == "banana"
    assert params["json"] == "1"
    assert params["page_size"] == "20"


@respx.mock
def test_search_sends_identifying_user_agent():
    route = respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([]))
    )
    svc = OFFService()

    svc.search("banana")

    headers = route.calls.last.request.headers
    assert "mandala-health" in headers["User-Agent"]


@respx.mock
def test_search_converts_kj_to_kcal_when_kcal_missing():
    product = off_product()
    del product["nutriments"]["energy-kcal_100g"]
    product["nutriments"]["energy_100g"] = 418.4  # kJ -> 100 kcal
    respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([product]))
    )
    svc = OFFService()

    (result,) = svc.search("x")

    assert result["kcal_per_100g"] == pytest.approx(100.0, rel=1e-3)


@respx.mock
def test_search_handles_missing_fields():
    product = {
        "code": "0001",
        "product_name": None,
        "nutriments": {},
    }
    respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([product]))
    )
    svc = OFFService()

    (result,) = svc.search("mystery")

    assert result["name"] == "Prodotto sconosciuto"
    assert result["brand"] is None
    assert result["kcal_per_100g"] == 0.0
    assert result["protein_per_100g"] == 0.0
    assert result["carbs_per_100g"] == 0.0
    assert result["fat_per_100g"] == 0.0


@respx.mock
def test_search_sorts_by_completeness_desc():
    p1 = off_product(code="1", name="Incomplete")
    p1["completeness"] = 0.2
    p2 = off_product(code="2", name="Complete")
    p2["completeness"] = 0.9
    respx.get(f"{BASE}/cgi/search.pl").mock(
        return_value=httpx.Response(200, json=off_search_response([p1, p2]))
    )
    svc = OFFService()

    results = svc.search("x")

    assert [r["name"] for r in results] == ["Complete", "Incomplete"]


@respx.mock
def test_search_network_error_raises_off_error():
    respx.get(f"{BASE}/cgi/search.pl").mock(side_effect=httpx.ConnectError("boom"))
    svc = OFFService()

    with pytest.raises(OFFError):
        svc.search("banana")


@respx.mock
def test_search_http_error_raises_off_error():
    respx.get(f"{BASE}/cgi/search.pl").mock(return_value=httpx.Response(503))
    svc = OFFService()

    with pytest.raises(OFFError):
        svc.search("banana")


@respx.mock
def test_get_by_barcode_returns_normalized_product_with_barcode():
    respx.get(f"{BASE}/api/v2/product/3017620422003.json").mock(
        return_value=httpx.Response(200, json={"status": 1, "product": off_product()})
    )
    svc = OFFService()

    result = svc.get_by_barcode("3017620422003")

    assert result["food_id"] == "3017620422003"
    assert result["name"] == "Nutella"
    assert result["brand"] == "Ferrero"
    assert result["kcal_per_100g"] == 539.0


@respx.mock
def test_get_by_barcode_unknown_product_raises_off_error():
    respx.get(f"{BASE}/api/v2/product/999.json").mock(
        return_value=httpx.Response(200, json={"status": 0})
    )
    svc = OFFService()

    with pytest.raises(OFFError):
        svc.get_by_barcode("999")
