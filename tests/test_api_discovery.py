"""Tests for discovery API endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestDiscoveryEndpoints:
    """Tests for discovery endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_get_data_summary_success(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test successful data summary request."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary?domain=geomag")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # Check nested structure: data.domain.geomag.stations.EYWM
        assert "domain" in data["data"]
        assert "geomag" in data["data"]["domain"]
        assert "stations" in data["data"]["domain"]["geomag"]
        assert "EYWM" in data["data"]["domain"]["geomag"]["stations"]
        mock_tilde_client.get_data_summary.assert_called_once_with(domain="geomag")

    def test_get_data_summary_default_domain(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test data summary with default domain."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary")

        assert response.status_code == 200
        mock_tilde_client.get_data_summary.assert_called_once_with(domain="geomag")

    def test_get_station_data_summary(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test getting data summary for specific station."""
        mock_cache_service.get.return_value = None  # Cache miss
        # Our implementation filters the domain summary, doesn't call with station parameter
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary/EYWM")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "station" in data["data"]
        assert data["data"]["station"]["station"] == "EYWM"
        # Should call with domain only (not station, since Tilde doesn't support it)
        mock_tilde_client.get_data_summary.assert_called_once_with(domain="geomag")

    def test_get_stations(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test getting list of stations."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/stations")

        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)
        assert "EYWM" in data["stations"]
        assert "TEST" in data["stations"]

    def test_get_stations_custom_domain(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test getting stations with custom domain."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/stations?domain=test")

        assert response.status_code == 200
        mock_tilde_client.get_data_summary.assert_called_once_with(domain="test")

    def test_data_summary_caching(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test that data summary responses are cached."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary")

        assert response.status_code == 200
        # Should set cache
        mock_cache_service.set.assert_called_once()
        # Should call Tilde API
        mock_tilde_client.get_data_summary.assert_called_once()

    def test_data_summary_cache_hit(self, client, mock_tilde_client, mock_cache_service, sample_data_summary):
        """Test that cached data summary is returned."""
        mock_cache_service.get.return_value = sample_data_summary  # Cache hit

        response = client.get("/api/v1/dataSummary")

        assert response.status_code == 200
        # Should not call Tilde API
        mock_tilde_client.get_data_summary.assert_not_called()
        # Should get from cache
        mock_cache_service.get.assert_called()

    def test_data_summary_error_handling(self, client, mock_tilde_client, mock_cache_service):
        """Test error handling for data summary."""
        from fastapi import HTTPException
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data_summary = AsyncMock(side_effect=HTTPException(status_code=404, detail="Not found"))

        response = client.get("/api/v1/dataSummary")

        assert response.status_code == 404
