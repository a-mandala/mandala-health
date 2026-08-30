"""Open Food Facts integration: single source of truth for foods.

Search and barcode lookup against the public OFF API, normalized to the
internal food dict shape (macros per 100 g). No local food table.
"""

import httpx

_KJ_PER_KCAL = 4.184

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{code}.json"


class OFFError(RuntimeError):
    """Open Food Facts is unreachable or returned an unusable response."""


class OFFNotFoundError(OFFError):
    """The requested product does not exist on Open Food Facts."""


USER_AGENT = (
    "mandala-health/0.1 (https://github.com/a-mandala/mandala-health; "
    "AGPL-3.0) httpx"
)


class OFFService:
    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    def search(self, query: str, page_size: int = 20) -> list[dict]:
        if not query.strip():
            return []
        try:
            resp = httpx.get(
                SEARCH_URL,
                params={
                    "search_terms": query.strip(),
                    "json": "1",
                    "page_size": page_size,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            products = resp.json().get("products") or []
        except (httpx.HTTPError, ValueError) as exc:
            raise OFFError(f"Open Food Facts unreachable: {exc}") from exc
        normalized = [self._normalize(p) for p in products if isinstance(p, dict)]
        normalized.sort(key=lambda f: f["_completeness"], reverse=True)
        return [{k: v for k, v in f.items() if k != "_completeness"} for f in normalized]

    def get_by_barcode(self, code: str) -> dict:
        try:
            resp = httpx.get(
                PRODUCT_URL.format(code=code),
                headers={"User-Agent": USER_AGENT},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            body = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OFFError(f"Open Food Facts unreachable: {exc}") from exc
        product = body.get("product")
        if not body.get("status") or not isinstance(product, dict):
            raise OFFNotFoundError(f"product {code!r} not found on Open Food Facts")
        return self._normalize(product)

    @staticmethod
    def _normalize(product: dict) -> dict:
        code = str(product.get("code") or "")
        nutriments = product.get("nutriments") or {}
        kcal = nutriments.get("energy-kcal_100g")
        if kcal is None and nutriments.get("energy_100g") is not None:
            kcal = float(nutriments["energy_100g"]) / _KJ_PER_KCAL

        def num(value) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        name = (product.get("product_name") or "").strip() or "Prodotto sconosciuto"
        brands = product.get("brands")
        brand = brands.strip() if isinstance(brands, str) and brands.strip() else None
        return {
            "food_id": code,
            "name": name,
            "brand": brand,
            "barcode": code,
            "kcal_per_100g": num(kcal),
            "protein_per_100g": num(nutriments.get("proteins_100g")),
            "carbs_per_100g": num(nutriments.get("carbohydrates_100g")),
            "fat_per_100g": num(nutriments.get("fat_100g")),
            "_completeness": num(product.get("completeness")),
        }


def get_off_service() -> OFFService:
    return OFFService()
