"""Tests for the seed script: JSON integrity + import into the DB."""

from app.integrations.food_db import FoodDatabase
from app.seed_foods import load_seed_foods


def test_seed_json_has_30_common_foods_with_all_macros():
    foods = load_seed_foods()

    assert len(foods) == 30
    for f in foods:
        assert {"name", "kcal_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g"} <= set(f)
        assert isinstance(f["name"], str) and f["name"]
    names = {f["name"] for f in foods}
    for expected in ("Pasta", "Riso", "Pollo (petto)", "Uova", "Latte intero", "Pane",
                     "Banana", "Mela", "Pomodoro", "Olio d'oliva", "Tonno (in scatola, al naturale)",
                     "Formaggio (emmenthal)", "Yogurt greco", "Avena (fiocchi)", "Lenticchie (secche)",
                     "Ceci (secchi)", "Manzo (magro)", "Salmone", "Patate", "Zucchero",
                     "Riso integrale", "Quinoa", "Tofu", "Mandorle", "Burro di arachidi",
                     "Miele", "Cioccolato fondente", "Vino rosso", "Birra", "Espresso"):
        assert expected in names


def test_seed_loads_into_database_and_is_idempotent(tmp_path):
    db = FoodDatabase(db_path=tmp_path / "foods.db")
    foods = load_seed_foods()

    added_first = db.load_seed(foods)
    added_second = db.load_seed(foods)

    assert added_first == 30
    assert added_second == 0
    assert [f["name"] for f in db.search("banana")] == ["Banana"]
