"""US-3: barcode scanner UI on the dashboard and the HTMX lookup flow."""

CODE = "9001"


def test_dashboard_has_barcode_scan_section(make_client):
    html = make_client().get("/").text

    # scan button, manual barcode fallback input, video preview, JS wiring
    assert 'id="scan-btn"' in html
    assert 'id="barcode-manual"' in html
    assert 'id="barcode-lookup-btn"' in html
    assert 'id="barcode-result"' in html
    assert 'id="barcode-video"' in html
    assert "/static/barcode.js" in html
    # mobile-first tap targets
    assert 'id="scan-btn"\n              class="w-full min-h-[44px]' in html


def test_barcode_js_is_served_locally(make_client):
    response = make_client().get("/static/barcode.js")

    assert response.status_code == 200
    js = response.text
    assert "BarcodeDetector" in js  # native API scanner path
    assert "/api/foods/barcode/" in js  # lookup via backend endpoint
    assert "getUserMedia" in js  # camera access with graceful fallback


def test_barcode_lookup_htmx_returns_confirmation_fragment(make_client):
    response = make_client().get(f"/api/foods/barcode/{CODE}", headers={"HX-Request": "true"})

    assert response.status_code == 200
    html = response.text
    assert "<html" not in html.lower()  # fragment, not full page
    assert "Banana" in html
    assert "89" in html  # kcal/100g shown for confirmation
    # confirm button carries the same data attributes as search results,
    # so the entry goes through the existing quick-log form
    assert 'data-food-id="9001"' in html
    assert 'data-kcal="89.0"' in html


def test_barcode_lookup_htmx_unknown_product_returns_error_fragment(make_client):
    response = make_client().get("/api/foods/barcode/0000", headers={"HX-Request": "true"})

    assert response.status_code == 200
    html = response.text
    assert "<html" not in html.lower()
    assert "trovato" in html.lower()


def test_barcode_lookup_htmx_off_down_returns_error_fragment(make_client):
    client = make_client()
    client.off.fail = True

    response = client.get(f"/api/foods/barcode/{CODE}", headers={"HX-Request": "true"})

    assert response.status_code == 200
    html = response.text
    assert "<html" not in html.lower()
    assert "errore" in html.lower() or "unreachable" in html.lower()
