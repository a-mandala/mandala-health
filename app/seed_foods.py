"""Seed the local food database with common foods from data/seed_foods.json.

Usage: python -m app.seed_foods
"""

import json
from pathlib import Path

from app.integrations.food_db import FoodDatabase, default_db_path

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_foods.json"


def load_seed_foods(path: Path | None = None) -> list[dict]:
    return json.loads((path or SEED_PATH).read_text())


def main() -> int:
    db = FoodDatabase(db_path=default_db_path())
    added = db.load_seed(load_seed_foods())
    print(f"seeded {added} foods into {default_db_path()}")
    return added


if __name__ == "__main__":
    main()
