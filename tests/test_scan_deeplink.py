"""US-3b: /scan deep-link — the phone's native barcode scanner opens
/scan?code=<barcode> and gets the product confirmation page pre-resolved,
so no browser camera permission is needed (works on plain HTTP in LAN).
"""

CODE = "9001"


def test_scan_with_code_renders_confirmation_page(make_client):
    response = make_client().get(f"/scan?code={CODE}")

    assert response.status_code == 200
    html = response.text
    assert "<html" in html.lower()  # full page, not an HTMX fragment
    assert "Banana" in html
    assert "89" in html  # kcal/100g
    # confirm button carries the same data attributes as search results,
    # so logging goes through the existing quick-log path
    assert 'data-food-id="9001"' in html
    assert 'data-kcal="89.0"' in html
    assert "/static/barcode.js" in html or "htmx" in html.lower()


def test_scan_without_code_renders_manual_form(make_client):
    response = make_client().get("/scan")

    assert response.status_code == 200
    html = response.text
    # form that GETs back to /scan with the code typed manually
    assert 'action="/scan"' in html
    assert 'name="code"' in html


def test_scan_unknown_code_renders_error_page(make_client):
    response = make_client().get("/scan?code=0000")

    assert response.status_code == 200
    html = response.text
    assert "trovato" in html.lower()


def test_scan_off_down_renders_error_page(make_client):
    client = make_client()
    client.off.fail = True

    response = client.get(f"/scan?code={CODE}")

    assert response.status_code == 200
    html = response.text
    assert "errore" in html.lower()
