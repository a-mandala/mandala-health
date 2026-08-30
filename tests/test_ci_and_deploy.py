"""US-2: CI workflow and deploy artifacts are present and well-formed."""

import pathlib
from unittest import mock

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def test_ci_workflow_exists():
    assert (REPO_ROOT / ".github/workflows/ci.yml").is_file()


@pytest.mark.skipif(yaml is None, reason="pyyaml not installed")
def test_ci_workflow_is_valid_yaml_and_runs_tests():
    data = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text())
    assert data is not None
    # triggers: pull_request + push to main
    on = data.get("on") or data.get(True)  # yaml 1.1 parses bare `on` as bool
    assert "pull_request" in on
    assert on["push"]["branches"] == ["main"]
    # steps include uv sync and pytest
    steps = data["jobs"]["test"]["steps"]
    runs = [s.get("run", "") for s in steps]
    assert any("uv sync" in r for r in runs)
    assert any("pytest" in r for r in runs)


def test_systemd_unit_exists():
    unit = (REPO_ROOT / "deploy/mandala-health.service").read_text()
    assert "[Service]" in unit
    assert "uvicorn" in unit
    assert "8020" in unit


def test_install_service_script_exists_and_executable():
    script = REPO_ROOT / "deploy/install-service.sh"
    assert script.is_file()
    assert script.read_text().startswith("#!")
    assert (script.stat().st_mode & 0o111)


def test_readme_documents_run_and_test_commands():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "uv run pytest" in readme
    assert "uvicorn" in readme or "uv run uvicorn" in readme
    assert "8020" in readme
    # systemd section
    assert "install-service.sh" in readme
    assert "loginctl enable-linger" in readme
    assert "systemctl --user" in readme
