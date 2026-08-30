"""Local diary store (SQLite `data/entries.db`).

Foods come from Open Food Facts; logged entries keep a minimal snapshot of
the food (code, name, brand, macros per 100 g) so the diary stays persistent
and the day summary works offline.
"""

import sqlite3
from datetime import date
from pathlib import Path

MEALS = ("breakfast", "lunch", "dinner", "snacks")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_code TEXT NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,
    kcal_per_100g REAL NOT NULL,
    protein_per_100g REAL NOT NULL,
    carbs_per_100g REAL NOT NULL,
    fat_per_100g REAL NOT NULL,
    grams REAL NOT NULL,
    meal TEXT NOT NULL,
    day TEXT NOT NULL
);
"""


def default_db_path() -> Path:
    return Path("data/entries.db")


class EntryStore:
    def __init__(self, db_path: Path | str | None = None):
        self._db_path = Path(db_path) if db_path else default_db_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    @property
    def path(self) -> Path:
        return self._db_path

    def log_entry(
        self,
        *,
        food_code: str,
        name: str,
        brand: str | None,
        kcal_per_100g: float,
        protein_per_100g: float,
        carbs_per_100g: float,
        fat_per_100g: float,
        grams: float,
        meal: str,
        day: str | None = None,
    ) -> int:
        if meal not in MEALS:
            raise ValueError(f"unknown meal: {meal!r}")
        cur = self._conn.execute(
            "INSERT INTO entries (food_code, name, brand, kcal_per_100g,"
            " protein_per_100g, carbs_per_100g, fat_per_100g, grams, meal, day)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                food_code, name, brand, kcal_per_100g, protein_per_100g,
                carbs_per_100g, fat_per_100g, grams, meal,
                day or date.today().isoformat(),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def entries_for(self, day: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM entries WHERE day = ? ORDER BY id", (day,)
        ).fetchall()
        return [dict(r) for r in rows]

    def day_summary(self, day: str | None = None) -> dict:
        day = day or date.today().isoformat()
        rows = self._conn.execute(
            "SELECT kcal_per_100g, protein_per_100g, carbs_per_100g,"
            " fat_per_100g, grams FROM entries WHERE day = ?",
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


def get_entry_store() -> EntryStore:
    return EntryStore()
