"""Tests for health, system, and error-handling endpoints.

These tests intentionally avoid real database or Groq connections: the
TestClient is used without entering its lifespan context, so the connection
pool is never initialized.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import APP_VERSION, settings
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sahayak-api"}


def test_database_health_returns_ok_when_connected():
    with patch("app.api.routes.health.check_database", return_value=True):
        response = client.get("/api/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_database_health_returns_safe_503_when_unavailable():
    from app.core.exceptions import DatabaseUnavailableError

    def raise_unavailable():
        raise DatabaseUnavailableError()

    with patch("app.api.routes.health.check_database", side_effect=raise_unavailable):
        response = client.get("/api/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "DATABASE_UNAVAILABLE", "message": "Database is unavailable."}
    }
    assert "postgresql" not in response.text


def test_system_info_returns_expected_fields():
    response = client.get("/api/system/info")
    assert response.status_code == 200
    assert response.json() == {
        "service": "sahayak-api",
        "environment": settings.app_env,
        "version": APP_VERSION,
    }


def test_system_info_does_not_leak_secrets():
    response = client.get("/api/system/info")
    text = response.text
    assert "gsk_" not in text
    assert "postgresql://" not in text
    assert "DATABASE_URL" not in text
    assert "GROQ_API_KEY" not in text
    assert "npg_" not in text


def test_unhandled_errors_return_safe_response():
    @app.get("/__test/boom", name="test_boom_route")
    def boom():
        raise RuntimeError("internal secret: postgresql://user:pass@host/db")

    response = client.get("/__test/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "Something went wrong."}
    }
    assert "internal secret" not in response.text
    assert "traceback" not in response.text.lower()


def test_unknown_route_returns_structured_404():
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "error" in body


def test_validation_errors_are_structured():
    @app.get("/__test/validate", name="test_validate_route")
    def validate(count: int):
        return {"count": count}

    response = client.get("/__test/validate?count=abc")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "stack" not in response.text.lower()