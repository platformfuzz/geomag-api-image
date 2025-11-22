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
