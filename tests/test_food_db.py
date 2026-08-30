"""TDD tests for the local FoodDatabase (SQLite) — search + custom foods."""

import pytest

from app.integrations.food_db import FoodDatabase


@pytest.fixture
def db(tmp_path):
    return FoodDatabase(db_path=tmp_path / "foods.db")


def test_add_custom_food_returns_id_and_search_finds_it(db):
    food_id = db.add_custom_food("Banana", 89.0, 1.1, 22.8, 0.3)

    assert isinstance(food_id, int)

    results = db.search("banana")

    assert len(results) == 1
    assert results[0] == {
        "food_id": food_id,
        "name": "Banana",
        "kcal_per_100g": 89.0,
        "protein_per_100g": 1.1,
        "carbs_per_100g": 22.8,
        "fat_per_100g": 0.3,
    }


def test_search_is_case_insensitive_and_partial(db):
    db.add_custom_food("Banana", 89.0, 1.1, 22.8, 0.3)
    db.add_custom_food("Pane integrale", 240.0, 9.0, 43.0, 3.5)

    assert db.search("BAN") == [db.search("ban")[0]]
    assert [f["name"] for f in db.search("ana")] == ["Banana"]
    assert [f["name"] for f in db.search("integrale")] == ["Pane integrale"]


def test_search_empty_query_returns_nothing(db):
    db.add_custom_food("Riso", 350.0, 7.0, 77.0, 1.0)

    assert db.search("") == []
