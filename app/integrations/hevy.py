"""Hevy integration: reads the latest workout via the Hevy REST API."""

import os

import httpx

HEVY_BASE_URL = "https://api.hevyapp.com/v1"
DEFAULT_API_KEY_PATH = "/home/mandala/.hevy/api_key"


def _load_api_key() -> str | None:
    env_key = os.environ.get("HEVY_API_KEY")
    if env_key:
        return env_key
    try:
        return open(DEFAULT_API_KEY_PATH).read().strip()
    except OSError:
        return None


def get_hevy_service() -> "HevyService":
    return HevyService()


class HevyService:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key if api_key is not None else _load_api_key()

    def last_workout(self) -> dict | None:
        """Latest workout, or None when unavailable (no API key, offline, empty)."""
        if not self._api_key:
            return None
        try:
            response = httpx.get(
                f"{HEVY_BASE_URL}/workouts",
                params={"page": 1, "pageSize": 1},
                headers={"api-key": self._api_key},
                timeout=15.0,
            )
            response.raise_for_status()
            workouts = response.json()["workouts"]
        except (httpx.HTTPError, KeyError, IndexError):
            return None
        workout = workouts[0]
        return {
            "date": workout["start_time"],
            "exercises": [
                {
                    "name": exercise["title"],
                    "sets": [
                        {"weight_kg": s.get("weight_kg"), "reps": s.get("reps")}
                        for s in exercise["sets"]
                    ],
                }
                for exercise in workout["exercises"]
            ],
        }
