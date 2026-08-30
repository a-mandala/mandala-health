"""Cronometer integration: wraps the cronometer-api-mcp client.

Choice: instead of duplicating the Cronometer client, we reuse the one
installed in /home/mandala/cronometer-api-mcp/.venv by adding its
site-packages to sys.path (documented in README). The client itself is
injected, so tests never touch the real API.
"""

import os
import sys
from pathlib import Path

_CRONOMETER_VENV = Path.home() / "cronometer-api-mcp" / ".venv"
CRONOMETER_ENV_PATH = _CRONOMETER_VENV.parent / ".env"


def _load_credentials_env(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = CRONOMETER_ENV_PATH
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _load_cronometer_client_class():
    try:
        from cronometer_api_mcp.client import CronometerClient
    except ImportError:
        for venv_dir in (_CRONOMETER_VENV, Path("/home/mandala") / _CRONOMETER_VENV.name):
            for site in venv_dir.glob("lib/python*/site-packages"):
                if str(site) not in sys.path:
                    sys.path.append(str(site))
            # the package is installed editable from <repo>/src
            src = venv_dir.parent / "src"
            if src.is_dir() and str(src) not in sys.path:
                sys.path.append(str(src))
        from cronometer_api_mcp.client import CronometerClient
    return CronometerClient


def get_cronometer_service() -> CronometerService:
    return CronometerService()


class CronometerService:
    def __init__(self, client=None):
        if client is None:
            _load_credentials_env()
            client = _load_cronometer_client_class()()
        self._client = client

    def get_day_summary(self, day=None) -> dict:
        data = self._client.get_consumed_nutrients(day)
        macros = data.get("macros", {})
        return {
            "energy": macros.get("energy"),
            "protein": macros.get("protein"),
            "carbs": macros.get("carbs"),
            "fat": macros.get("fat"),
        }
