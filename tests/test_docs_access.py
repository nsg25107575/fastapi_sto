"""Tests for production lockdown of the interactive API docs.

`GET /docs` (custom Swagger page, main.py) and `GET /openapi.json`
(FastAPI's built-in schema route) must be publicly reachable in
development but return 404 whenever `Config.app_env` is anything other
than `"development"` -- a default-deny posture so a missing/misconfigured
`APP_ENV` fails safe (blocked) rather than fails open (exposed), which is
what happened in production prior to this fix.
"""
from config import Config


def test_docs_accessible_in_development(client, monkeypatch):
    monkeypatch.setattr(Config, "app_env", "development")

    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_openapi_json_accessible_in_development(client, monkeypatch):
    monkeypatch.setattr(Config, "app_env", "development")

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "FastAPI"


def test_docs_blocked_in_production(client, monkeypatch):
    monkeypatch.setattr(Config, "app_env", "production")

    response = client.get("/docs")

    assert response.status_code == 404


def test_openapi_json_blocked_in_production(client, monkeypatch):
    monkeypatch.setattr(Config, "app_env", "production")

    response = client.get("/openapi.json")

    assert response.status_code == 404


def test_docs_blocked_when_app_env_unset_or_unknown(client, monkeypatch):
    """Default-deny: any value other than the literal 'development'
    string blocks the docs -- including unexpected/misconfigured values,
    not just the exact string 'production'."""
    monkeypatch.setattr(Config, "app_env", "staging")

    response = client.get("/docs")

    assert response.status_code == 404
