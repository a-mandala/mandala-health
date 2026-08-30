"""Local food database (SQLite): replaces the Cronometer integration.

Foods are stored with macros per 100 g; logged entries scale them by the
logged grams. The DB lives at `data/foods.db` (mounted as a Docker volume)
and can be populated with `python -m app.seed_foods`.
"""

import sqlite3
from datetime import date
from pathlib import Path

MEALS = ("breakfast", "lunch", "dinner", "snacks")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    kcal_per_100g REAL NOT NULL,
    protein_per_100g REAL NOT NULL,
    carbs_per_100g REAL NOT NULL,
    fat_per_100g REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_id INTEGER NOT NULL REFERENCES foods(id),
    grams REAL NOT NULL,
    meal TEXT NOT NULL,
    day TEXT NOT NULL
);
"""


def default_db_path() -> Path:
    return Path("data/foods.db")


class FoodDatabase:
    def __init__(self, db_path: Path | str | None = None):
        self._db_path = Path(db_path) if db_path else default_db_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def search(self, query: str) -> list[dict]:
        query = query.strip().lower()
        if not query:
            return []
        rows = self._conn.execute(
            "SELECT * FROM foods WHERE lower(name) LIKE ? ORDER BY name",
            (f"%{query}%",),
        ).fetchall()
        return [self._food_dict(r) for r in rows]

    def add_custom_food(
        self, name: str, kcal: float, protein: float, carbs: float, fat: float
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO foods (name, kcal_per_100g, protein_per_100g,"
            " carbs_per_100g, fat_per_100g) VALUES (?, ?, ?, ?, ?)",
            (name, kcal, protein, carbs, fat),
        )
        self._conn.commit()
        return cur.lastrowid

    def log_entry(self, food_id: int, grams: float, meal: str, day: str | None = None) -> int:
        if meal not in MEALS:
            raise ValueError(f"unknown meal: {meal!r}")
        cur = self._conn.execute(
            "INSERT INTO entries (food_id, grams, meal, day) VALUES (?, ?, ?, ?)",
            (food_id, grams, meal, day or date.today().isoformat()),
        )
        self._conn.commit()
        return cur.lastrowid

    def day_summary(self, day: str | None = None) -> dict:
        day = day or date.today().isoformat()
        rows = self._conn.execute(
            "SELECT f.kcal_per_100g, f.protein_per_100g, f.carbs_per_100g,"
            " f.fat_per_100g, e.grams"
            " FROM entries e JOIN foods f ON f.id = e.food_id WHERE e.day = ?",
            (day,),
        ).fetchall()
        summary = {"energy": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for r in rows:
            scale = r["grams"] / 100.0
            summary["energy"] += r["kcal_per_100g"] * scale
            summary["protein"] += r["protein_per_100g"] * scale
            summary["carbs"] += r["carbs_per_100g"] * scale
            summary["fat"] += r["fat_per_100g"] * scale
        return summary

    def load_seed(self, foods: list[dict]) -> int:
        """Bulk-insert seed foods (skipping names already present). Returns count added."""
        existing = {
            r["name"].lower()
            for r in self._conn.execute("SELECT name FROM foods").fetchall()
        }
        added = 0
        for f in foods:
            if f["name"].lower() in existing:
                continue
            self.add_custom_food(
                f["name"],
                f["kcal_per_100g"],
                f["protein_per_100g"],
                f["carbs_per_100g"],
                f["fat_per_100g"],
            )
            added += 1
        return added

    @staticmethod
    def _food_dict(row: sqlite3.Row) -> dict:
        return {
            "food_id": row["id"],
            "name": row["name"],
            "kcal_per_100g": row["kcal_per_100g"],
            "protein_per_100g": row["protein_per_100g"],
            "carbs_per_100g": row["carbs_per_100g"],
            "fat_per_100g": row["fat_per_100g"],
        }


def get_food_db_service() -> FoodDatabase:
    return FoodDatabase()
