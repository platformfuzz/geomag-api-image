"""Tests for main application."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestMainApp:
    """Tests for main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "GeoNet Geomag API"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "geomag-api"

    def test_openapi_docs_available(self, client):
        """Test that OpenAPI docs are available."""
        response = client.get("/docs")

        # Should redirect or return HTML
        assert response.status_code in [200, 307, 308]

    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "GeoNet Geomag API"

    def test_cors_preflight_request(self, client):
        """Test CORS preflight OPTIONS request."""
        # Use a GET endpoint that supports OPTIONS for preflight
        response = client.options(
            "/health",
            headers={"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"}
        )
        # OPTIONS may return 200 (handled by CORS) or 405 (endpoint doesn't support OPTIONS)
        # Either way, CORS headers should be present if status is 200
        if response.status_code == 200:
            assert "access-control-allow-origin" in response.headers
            # When WEB_ORIGIN is "*", it returns "*", otherwise returns the specific origin
            assert response.headers["access-control-allow-origin"] in ["*", "http://localhost:8080"]

    def test_cors_headers_in_get_request(self, client):
        """Test CORS headers in GET request."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_localhost_8080(self, client):
        """Test that localhost:8080 is allowed when WEB_ORIGIN is '*' (default)."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:8080"}
        )
        assert response.status_code == 200
        # When WEB_ORIGIN is "*" (default), CORS returns "*" for all origins
        assert response.headers["access-control-allow-origin"] == "*"

    def test_cors_allows_localhost_3000(self, client):
        """Test that localhost:3000 is allowed when WEB_ORIGIN is '*' (default)."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        # When WEB_ORIGIN is "*" (default), CORS returns "*" for all origins
        assert response.headers["access-control-allow-origin"] == "*"

    def test_cors_without_origin_header(self, client):
        """Test that requests without Origin header still work (backward compatibility)."""
        response = client.get("/health")
        assert response.status_code == 200
        # Should still work, CORS headers may or may not be present
