"""Tests for CronometerService default client construction (env loading)."""

import os

import app.integrations.cronometer as cronometer_module
from app.integrations.cronometer import CronometerService


def test_default_construction_loads_credentials_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "CRONOMETER_USERNAME=me@example.com\nCRONOMETER_PASSWORD=secret\n"
    )
    monkeypatch.delenv("CRONOMETER_USERNAME", raising=False)
    monkeypatch.delenv("CRONOMETER_PASSWORD", raising=False)
    monkeypatch.setattr(cronometer_module, "CRONOMETER_ENV_PATH", env_file)
    monkeypatch.setattr(
        cronometer_module,
        "_load_cronometer_client_class",
        lambda: _RecordingClientClass,
    )

    class _RecordingClientClass:
        last_init_kwargs = None

        def __init__(self, **kwargs):
            _RecordingClientClass.last_init_kwargs = kwargs

    CronometerService()

    assert os.environ["CRONOMETER_USERNAME"] == "me@example.com"
    assert os.environ["CRONOMETER_PASSWORD"] == "secret"
