"""Cronometer integration: wraps the cronometer-api-mcp client.

Choice: instead of duplicating the Cronometer client, we reuse the one
installed in /home/mandala/cronometer-api-mcp/.venv by adding its
site-packages to sys.path (documented in README). The client itself is
injected, so tests never touch the real API.
"""

import os
import sys
from pathlib import Path

_CRONOMETER_VENV = Path.home() / "cronometer-api-mcp" / ".venv"
CRONOMETER_ENV_PATH = _CRONOMETER_VENV.parent / ".env"


def _load_credentials_env(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = CRONOMETER_ENV_PATH
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _load_cronometer_client_class():
    try:
        from cronometer_api_mcp.client import CronometerClient
    except ImportError:
        for venv_dir in (_CRONOMETER_VENV, Path("/home/mandala") / _CRONOMETER_VENV.name):
            for site in venv_dir.glob("lib/python*/site-packages"):
                if str(site) not in sys.path:
                    sys.path.append(str(site))
            # the package is installed editable from <repo>/src
            src = venv_dir.parent / "src"
            if src.is_dir() and str(src) not in sys.path:
                sys.path.append(str(src))
        from cronometer_api_mcp.client import CronometerClient
    return CronometerClient


def get_cronometer_service() -> CronometerService:
    return CronometerService()


class CronometerService:
    def __init__(self, client=None):
        if client is None:
            _load_credentials_env()
            client = _load_cronometer_client_class()()
        self._client = client

    def get_day_summary(self, day=None) -> dict:
        data = self._client.get_consumed_nutrients(day)
        macros = data.get("macros", {})
        return {
            "energy": macros.get("energy"),
            "protein": macros.get("protein"),
            "carbs": macros.get("carbs"),
            "fat": macros.get("fat"),
        }

    def search_foods(self, query: str) -> list[dict]:
        """Search foods and normalize results with per-100g macros.

        Design note: search_food() results do not include nutrient values,
        so we batch-fetch full details via get_foods(), whose nutrients are
        already stored per-100g — no manual scaling needed. One extra call
        per search, but it keeps kcal visible in the UI autocomplete.
        """
        raw = self._client.search_food(query)
        foods = self._client.get_foods([f["id"] for f in raw])
        by_id = {f.get("id"): f for f in foods}
        results = []
        for item in raw:
            detail = by_id.get(item["id"], {})
            nutrients = detail.get("nutrients", {}) or {}
            results.append(
                {
                    "food_id": item["id"],
                    "measure_id": item.get("measureId"),
                    "name": item.get("name"),
                    "source": item.get("source"),
                    "measure_display": item.get("measureDisplayName"),
                    "kcal_per_100g": nutrients.get("energy"),
                    "protein_per_100g": nutrients.get("protein"),
                }
            )
        return results

    MEAL_GROUPS = {"breakfast": 1, "lunch": 2, "dinner": 3, "snacks": 4}

    def add_food_entry(self, food_id: int, measure_id: int, grams: float, meal: str) -> dict:
        """Log a serving to today's diary. `meal` is a name mapped to
        the client's integer diary_group (1=breakfast … 4=snacks)."""
        if meal not in self.MEAL_GROUPS:
            raise ValueError(f"unknown meal: {meal!r}")
        return self._client.add_serving(
            food_id=food_id,
            measure_id=measure_id,
            grams=grams,
            diary_group=self.MEAL_GROUPS[meal],
        )
