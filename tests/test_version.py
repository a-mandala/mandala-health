"""TDD tests for visible version: /api/version endpoint + dashboard footer."""

from fastapi.testclient import TestClient

from app import main


def test_version_endpoint_returns_version_git_hash_build_date(make_client):
    response = make_client().get("/api/version")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"version", "git_hash", "build_date"}


def test_version_falls_back_to_dev_without_git(monkeypatch):
    from app import version as version_module

    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("APP_GIT_HASH", raising=False)
    monkeypatch.delenv("APP_BUILD_DATE", raising=False)
    monkeypatch.setattr(version_module, "_git_describe", lambda: None)

    info = version_module.version_info()

    assert info["version"] == "dev"
    assert info["git_hash"] == "dev"


def test_version_reads_build_env(monkeypatch):
    from app import version as version_module

    monkeypatch.setenv("APP_VERSION", "v1.2.3")
    monkeypatch.setenv("APP_GIT_HASH", "abc1234")
    monkeypatch.setenv("APP_BUILD_DATE", "2026-08-30")

    info = version_module.version_info()

    assert info == {"version": "v1.2.3", "git_hash": "abc1234", "build_date": "2026-08-30"}


def test_dashboard_footer_shows_clickable_version(make_client):
    html = make_client().get("/").text

    assert 'href="/api/version"' in html
    assert "v" in html  # "v<hash>" label
    # discreet styling
    assert "text-slate-500" in html
    assert "text-xs" in html
