"""API tests for GET /health."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    """The health endpoint must always return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_structure() -> None:
    """The response body must contain the expected fields."""
    response = client.get("/health")
    body = response.json()

    assert "status" in body
    assert "service" in body
    assert "version" in body
    assert "database" in body


def test_health_status_is_ok() -> None:
    """The service-level status field must be ''ok''."""
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"


def test_health_service_name() -> None:
    """The service name must match the configured application name."""
    response = client.get("/health")
    body = response.json()
    assert body["service"] == "Employee Operations AI"


def test_health_version() -> None:
    """The version field must be a non-empty string."""
    response = client.get("/health")
    body = response.json()
    assert body["version"]


def test_health_database_field_is_valid_value() -> None:
    """The database field must be either ''ok'' or ''unavailable''."""
    response = client.get("/health")
    body = response.json()
    assert body["database"] in {"ok", "unavailable"}