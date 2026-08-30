"""TDD tests for FoodDatabase logging and day summary."""

import pytest

from app.integrations.food_db import FoodDatabase


@pytest.fixture
def db(tmp_path):
    db = FoodDatabase(db_path=tmp_path / "foods.db")
    db.pasta_id = db.add_custom_food("Pasta", 350.0, 12.0, 70.0, 1.5)
    db.pollo_id = db.add_custom_food("Pollo", 165.0, 31.0, 0.0, 3.6)
    return db


def test_log_entry_scales_macros_by_grams(db):
    db.log_entry(db.pasta_id, 200.0, "lunch")

    summary = db.day_summary()

    assert summary == {"energy": 700.0, "protein": 24.0, "carbs": 140.0, "fat": 3.0}


def test_day_summary_sums_multiple_entries(db):
    db.log_entry(db.pasta_id, 100.0, "lunch")
    db.log_entry(db.pollo_id, 150.0, "dinner")

    summary = db.day_summary()

    # 350 + 165*1.5 = 597.5 kcal
    assert summary["energy"] == pytest.approx(597.5)
    assert summary["protein"] == pytest.approx(12.0 + 31.0 * 1.5)


def test_day_summary_only_counts_requested_day(db):
    db.log_entry(db.pasta_id, 100.0, "lunch", day="2026-08-29")
    db.log_entry(db.pollo_id, 100.0, "dinner", day="2026-08-30")

    assert db.day_summary("2026-08-29")["energy"] == pytest.approx(350.0)
    assert db.day_summary("2026-08-30")["energy"] == pytest.approx(165.0)
    assert db.day_summary("2026-01-01")["energy"] == 0.0


@pytest.mark.parametrize("meal", ["breakfast", "lunch", "dinner", "snacks"])
def test_log_entry_accepts_the_four_meals(db, meal):
    assert isinstance(db.log_entry(db.pasta_id, 50.0, meal), int)


@pytest.mark.parametrize("meal", ["brunch", "", "colazione", 1])
def test_log_entry_rejects_unknown_meal(db, meal):
    with pytest.raises(ValueError):
        db.log_entry(db.pasta_id, 50.0, meal)
