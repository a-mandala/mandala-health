"""TDD tests for the local entries store (SQLite data/entries.db).

The diary persists minimal food snapshots from Open Food Facts; the day
summary is computed from logged entries, offline.
"""

import pytest

from app.integrations.entries import EntryStore


@pytest.fixture
def store(tmp_path):
    return EntryStore(db_path=tmp_path / "entries.db")


def test_log_entry_persists_food_snapshot(store):
    entry_id = store.log_entry(
        food_code="3017620422003",
        name="Nutella",
        brand="Ferrero",
        kcal_per_100g=539.0,
        protein_per_100g=6.3,
        carbs_per_100g=57.5,
        fat_per_100g=30.9,
        grams=30.0,
        meal="breakfast",
        day="2026-08-30",
    )

    assert isinstance(entry_id, int)
    rows = store.entries_for("2026-08-30")
    assert len(rows) == 1
    assert rows[0]["food_code"] == "3017620422003"
    assert rows[0]["name"] == "Nutella"
    assert rows[0]["brand"] == "Ferrero"
    assert rows[0]["kcal_per_100g"] == 539.0
    assert rows[0]["grams"] == 30.0
    assert rows[0]["meal"] == "breakfast"


def test_day_summary_scales_kcal_by_grams(store):
    store.log_entry(
        food_code="1", name="Banana", brand=None, kcal_per_100g=89.0,
        protein_per_100g=1.1, carbs_per_100g=22.8, fat_per_100g=0.3,
        grams=200.0, meal="breakfast", day="2026-08-30",
    )

    summary = store.day_summary("2026-08-30")

    assert summary["energy"] == pytest.approx(178.0)  # 89 * 200 / 100
    assert summary["protein"] == pytest.approx(2.2)
    assert summary["carbs"] == pytest.approx(45.6)
    assert summary["fat"] == pytest.approx(0.6)


def test_day_summary_only_counts_requested_day(store):
    store.log_entry(
        food_code="1", name="Banana", brand=None, kcal_per_100g=89.0,
        protein_per_100g=1.1, carbs_per_100g=22.8, fat_per_100g=0.3,
        grams=100.0, meal="lunch", day="2026-08-29",
    )

    assert store.day_summary("2026-08-29")["energy"] == pytest.approx(89.0)
    assert store.day_summary("2026-08-30")["energy"] == 0.0


def test_day_summary_sums_multiple_entries(store):
    store.log_entry(
        food_code="1", name="Pasta", brand=None, kcal_per_100g=350.0,
        protein_per_100g=12.0, carbs_per_100g=70.0, fat_per_100g=1.5,
        grams=100.0, meal="lunch", day="2026-08-30",
    )
    store.log_entry(
        food_code="2", name="Pollo", brand=None, kcal_per_100g=165.0,
        protein_per_100g=31.0, carbs_per_100g=0.0, fat_per_100g=3.6,
        grams=150.0, meal="dinner", day="2026-08-30",
    )

    summary = store.day_summary("2026-08-30")

    assert summary["energy"] == pytest.approx(350.0 + 247.5)
    assert summary["protein"] == pytest.approx(12.0 + 46.5)


def test_log_entry_rejects_unknown_meal(store):
    with pytest.raises(ValueError):
        store.log_entry(
            food_code="1", name="X", brand=None, kcal_per_100g=100.0,
            protein_per_100g=0.0, carbs_per_100g=0.0, fat_per_100g=0.0,
            grams=50.0, meal="brunch",
        )


def test_log_entry_defaults_to_today(store):
    from datetime import date

    store.log_entry(
        food_code="1", name="X", brand=None, kcal_per_100g=100.0,
        protein_per_100g=0.0, carbs_per_100g=0.0, fat_per_100g=0.0,
        grams=50.0, meal="snacks",
    )

    today = date.today().isoformat()
    assert store.entries_for(today)[0]["day"] == today
