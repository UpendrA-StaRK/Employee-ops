"""Unit tests for REST API source ingestion.

All HTTP calls are intercepted by `respx` — no real network traffic is made.
respx is the standard httpx mocking companion and integrates cleanly with
the project's existing httpx dependency.
"""
import json
import pytest
import respx
import httpx

from app.pipelines.rest_ingestion import ingest_rest

BASE_URL = "http://mock-reference-service/departments"

SAMPLE_DEPARTMENTS = [
    {"code": "HR", "name": "Human Resources"},
    {"code": "ENG", "name": "Engineering"},
    {"code": "FIN", "name": "Finance"},
]


class TestRestIngestionSuccess:
    """Happy path: valid JSON array returned from the endpoint."""

    @respx.mock
    def test_returns_list_of_dicts(self):
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_DEPARTMENTS)
        )
        data = ingest_rest(BASE_URL)
        assert isinstance(data, list)
        assert len(data) == 3

    @respx.mock
    def test_correct_keys_returned(self):
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json=SAMPLE_DEPARTMENTS)
        )
        data = ingest_rest(BASE_URL)
        assert set(data[0].keys()) == {"code", "name"}

    @respx.mock
    def test_empty_list_is_valid(self):
        """An empty JSON array is a valid successful response."""
        respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=[]))
        data = ingest_rest(BASE_URL)
        assert data == []


class TestRestIngestionHttpErrors:
    """HTTP 4xx and 5xx responses must raise RuntimeError."""

    @respx.mock
    def test_404_raises_runtime_error(self):
        respx.get(BASE_URL).mock(return_value=httpx.Response(404))
        with pytest.raises(RuntimeError, match="HTTP 404"):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_401_raises_runtime_error(self):
        respx.get(BASE_URL).mock(return_value=httpx.Response(401))
        with pytest.raises(RuntimeError, match="HTTP 401"):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_500_raises_runtime_error(self):
        respx.get(BASE_URL).mock(return_value=httpx.Response(500))
        with pytest.raises(RuntimeError, match="HTTP 500"):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_503_raises_runtime_error(self):
        respx.get(BASE_URL).mock(return_value=httpx.Response(503))
        with pytest.raises(RuntimeError, match="HTTP 503"):
            ingest_rest(BASE_URL)


class TestRestIngestionNetworkFailures:
    """Network-level failures must raise ConnectionError."""

    @respx.mock
    def test_connection_refused_raises_connection_error(self):
        respx.get(BASE_URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(ConnectionError):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_timeout_raises_connection_error(self):
        respx.get(BASE_URL).mock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        with pytest.raises(ConnectionError):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_dns_failure_raises_connection_error(self):
        respx.get(BASE_URL).mock(side_effect=httpx.ConnectError("Name resolution failed"))
        with pytest.raises(ConnectionError):
            ingest_rest(BASE_URL)


class TestRestIngestionMalformedResponse:
    """Non-JSON or unexpected JSON structure must raise ValueError."""

    @respx.mock
    def test_html_response_raises_value_error(self):
        """Server returns HTML instead of JSON (e.g. a proxy error page)."""
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(
                200, content=b"<html>Not JSON</html>",
                headers={"content-type": "text/html"},
            )
        )
        with pytest.raises(ValueError, match="non-JSON"):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_json_object_raises_value_error(self):
        """Server returns a JSON object instead of an array."""
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, json={"error": "unexpected"})
        )
        with pytest.raises(ValueError, match="unexpected type"):
            ingest_rest(BASE_URL)

    @respx.mock
    def test_json_string_raises_value_error(self):
        """Server returns a bare JSON string instead of an array."""
        respx.get(BASE_URL).mock(
            return_value=httpx.Response(200, content=b'"just a string"')
        )
        with pytest.raises(ValueError, match="unexpected type"):
            ingest_rest(BASE_URL)


class TestRestIngestionMockServer:
    """Smoke test against the mock FastAPI server using TestClient."""

    def test_mock_server_departments_endpoint(self):
        """Verify the mock server returns the expected reference data."""
        from fastapi.testclient import TestClient
        from app.pipelines.mock_rest.server import mock_app

        with TestClient(mock_app) as client:
            response = client.get("/departments")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert all("code" in d and "name" in d for d in data)

    def test_mock_server_job_titles_endpoint(self):
        """Verify the mock server's job-titles endpoint."""
        from fastapi.testclient import TestClient
        from app.pipelines.mock_rest.server import mock_app

        with TestClient(mock_app) as client:
            response = client.get("/job-titles")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
