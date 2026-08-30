"""Shared fixtures: TestClient with fake OFF, real (tmp) EntryStore, fake Hevy."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.integrations.entries import EntryStore, get_entry_store
from app.integrations.hevy import get_hevy_service
from app.integrations.off import OFFError, OFFNotFoundError, get_off_service

BANANA = {
    "food_id": "9001",
    "name": "Banana",
    "brand": None,
    "barcode": "9001",
    "kcal_per_100g": 89.0,
    "protein_per_100g": 1.1,
    "carbs_per_100g": 22.8,
    "fat_per_100g": 0.3,
}

NUTELLA = {
    "food_id": "3017620422003",
    "name": "Nutella",
    "brand": "Ferrero",
    "barcode": "3017620422003",
    "kcal_per_100g": 539.0,
    "protein_per_100g": 6.3,
    "carbs_per_100g": 57.5,
    "fat_per_100g": 30.9,
}


class FakeOFF:
    """Offline stand-in for OFFService; tests manipulate its state directly."""

    def __init__(self):
        self.catalog = [BANANA, NUTELLA]
        self.fail = False

    def search(self, query: str) -> list[dict]:
        if self.fail:
            raise OFFError("Open Food Facts unreachable")
        q = query.strip().lower()
        return [f for f in self.catalog if q and q in f["name"].lower()]

    def get_by_barcode(self, code: str) -> dict:
        if self.fail:
            raise OFFError("Open Food Facts unreachable")
        for f in self.catalog:
            if f["barcode"] == code:
                return f
        raise OFFNotFoundError(f"product {code!r} not found on Open Food Facts")


class FakeHevy:
    def last_workout(self):
        return {
            "date": "2026-08-30T09:10:55+00:00",
            "exercises": [
                {"name": "Lat Pulldown", "sets": [{"weight_kg": 55, "reps": 10}]}
            ],
        }


@pytest.fixture
def make_client(tmp_path):
    """Fresh app client: fake OFF + real EntryStore in tmp_path.

    Optionally pre-logs 200 g of banana at breakfast (=> 178 kcal, 2.2 g
    protein). The client exposes `off` (FakeOFF) and `store` (EntryStore).
    """

    def _make(log_banana: bool = True):
        off = FakeOFF()
        store = EntryStore(db_path=tmp_path / "entries.db")
        if log_banana:
            store.log_entry(
                food_code="9001", name="Banana", brand=None,
                kcal_per_100g=89.0, protein_per_100g=1.1,
                carbs_per_100g=22.8, fat_per_100g=0.3,
                grams=200.0, meal="breakfast",
            )
        main.app.dependency_overrides[get_off_service] = lambda: off
        main.app.dependency_overrides[get_entry_store] = lambda: store
        main.app.dependency_overrides[get_hevy_service] = lambda: FakeHevy()
        client = TestClient(main.app)
        client.off = off
        client.store = store
        return client

    return _make
