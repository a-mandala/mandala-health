"""Auto-seed on startup: a fresh DB must be searchable without manual seeding."""

import shutil
from pathlib import Path

from app import main
from app.integrations.food_db import FoodDatabase, get_food_db_service
from app.seed_foods import SEED_PATH, ensure_seeded
from fastapi.testclient import TestClient

REAL_SEED = Path(__file__).resolve().parent.parent / "data" / "seed_foods.json"


def test_ensure_seeded_populates_fresh_db(tmp_path):
    seed = tmp_path / "seed.json"
    shutil.copy(REAL_SEED, seed)
    db = FoodDatabase(db_path=tmp_path / "foods.db")

    added = ensure_seeded(db, seed_path=seed)

    assert added >= 1
    assert len(db.search("banana")) >= 1


def test_ensure_seeded_is_idempotent(tmp_path):
    from app.integrations.food_db import FoodDatabase

    db = FoodDatabase(db_path=tmp_path / "foods.db")
    ensure_seeded(db, seed_path=REAL_SEED)

    added_again = ensure_seeded(db, seed_path=REAL_SEED)

    assert added_again == 0


def test_ensure_seeded_missing_file_warns_and_does_not_crash(tmp_path, caplog):
    from app.integrations.food_db import FoodDatabase

    db = FoodDatabase(db_path=tmp_path / "foods.db")

    added = ensure_seeded(db, seed_path=tmp_path / "missing.json")

    assert added == 0
    assert db.search("banana") == []
    assert any("seed" in r.message.lower() for r in caplog.records)


def test_factory_autoseeds_default_db(tmp_path, monkeypatch):
    """get_food_db_service on a fresh cwd must auto-seed from the repo seed file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    db = get_food_db_service()

    assert len(db.search("banana")) >= 1


def test_search_endpoint_works_on_fresh_unseeded_db(tmp_path, monkeypatch):
    """End-to-end: fresh default DB + real seed file => /api/foods/search finds Banana."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    main.app.dependency_overrides.clear()
    client = TestClient(main.app)

    resp = client.get("/api/foods/search", params={"q": "banana"})

    assert resp.status_code == 200
    assert any(r["name"] == "Banana" for r in resp.json())


def test_seed_path_constant_points_at_repo_seed_file():
    assert SEED_PATH.name == "seed_foods.json"
    assert SEED_PATH.exists()
