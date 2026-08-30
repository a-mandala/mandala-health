"""Seed the local food database with common foods from data/seed_foods.json.

Usage: python -m app.seed_foods
"""

import json
import logging
from pathlib import Path

from app.integrations.food_db import FoodDatabase, default_db_path

logger = logging.getLogger(__name__)

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_foods.json"


def load_seed_foods(path: Path | None = None) -> list[dict]:
    return json.loads((path or SEED_PATH).read_text())


def ensure_seeded(db: FoodDatabase, seed_path: Path | None = None) -> int:
    """Seed `db` from the JSON seed file if it has no foods yet.

    Idempotent: does nothing when the foods table is already populated.
    A missing seed file logs a warning instead of crashing (the app must
    boot even without seed data).
    """
    path = seed_path or SEED_PATH
    if db.food_count() > 0:
        return 0
    if not path.exists():
        logger.warning("seed file %s not found: food DB left empty", path)
        return 0
    added = db.load_seed(load_seed_foods(path))
    if added:
        logger.info("auto-seeded %d foods from %s into %s", added, path, db.path)
    return added


def main() -> int:
    db = FoodDatabase(db_path=default_db_path())
    added = db.load_seed(load_seed_foods())
    print(f"seeded {added} foods into {default_db_path()}")
    return added


if __name__ == "__main__":
    main()
