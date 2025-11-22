"""Tests for data API endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestDataEndpoints:
    """Tests for data endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_get_latest_data_success(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test successful latest data request."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        mock_tilde_client.get_data.assert_called_once_with(
            domain="geomag",
            station="EYWM",
            name="magnetic-field-component",
            sensor_code="50",
            method="60s",
            aspect="X-magnetic-north",
            period="6h"
        )

    def test_get_latest_data_invalid_period(self, client):
        """Test latest data with invalid period format."""
        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/invalid"
        )

        assert response.status_code == 400
        assert "Period must be in format" in response.json()["detail"]

    def test_get_data_range_success(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test successful date range request."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-01-20/2025-01-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        mock_tilde_client.get_data.assert_called_once_with(
            domain="geomag",
            station="EYWM",
            name="magnetic-field-component",
            sensor_code="50",
            method="60s",
            aspect="X-magnetic-north",
            start_date="2025-01-20",
            end_date="2025-01-21"
        )

    def test_get_data_range_invalid_date(self, client):
        """Test date range with invalid date format."""
        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-01-20/invalid"
        )

        assert response.status_code == 400
        assert "YYYY-MM-DD" in response.json()["detail"]

    def test_get_data_day_success(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test successful single day request."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-01-20"
        )

        assert response.status_code == 200
        # Should call get_data_range with same start and end date
        mock_tilde_client.get_data.assert_called_once_with(
            domain="geomag",
            station="EYWM",
            name="magnetic-field-component",
            sensor_code="50",
            method="60s",
            aspect="X-magnetic-north",
            start_date="2025-01-20",
            end_date="2025-01-20"
        )

    def test_get_station_latest_data_defaults(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test convenience endpoint with default parameters."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get("/api/v1/data/EYWM/latest/6h")

        assert response.status_code == 200
        mock_tilde_client.get_data.assert_called_once_with(
            domain="geomag",
            station="EYWM",
            name="magnetic-field-component",
            sensor_code="50",
            method="60s",
            aspect="X-magnetic-north",
            period="6h"
        )

    def test_get_station_latest_data_custom_params(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test convenience endpoint with custom parameters."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/latest/6h?"
            "name=magnetic-field&sensor_code=60&method=1s&aspect=Y-magnetic-east"
        )

        assert response.status_code == 200
        mock_tilde_client.get_data.assert_called_once_with(
            domain="geomag",
            station="EYWM",
            name="magnetic-field",
            sensor_code="60",
            method="1s",
            aspect="Y-magnetic-east",
            period="6h"
        )

    def test_data_caching_latest(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test that latest data responses are cached."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 200
        # Should set cache with is_latest=True
        mock_cache_service.set.assert_called_once()
        call_kwargs = mock_cache_service.set.call_args[1]
        assert call_kwargs["is_latest"] is True

    def test_data_caching_historical(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test that historical data responses are cached."""
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(return_value=sample_data_response)

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-01-20/2025-01-21"
        )

        assert response.status_code == 200
        # Should set cache with is_latest=False
        mock_cache_service.set.assert_called_once()
        call_kwargs = mock_cache_service.set.call_args[1]
        assert call_kwargs["is_latest"] is False

    def test_data_cache_hit(self, client, mock_tilde_client, mock_cache_service, sample_data_response):
        """Test that cached data is returned."""
        mock_cache_service.get.return_value = sample_data_response  # Cache hit

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 200
        # Should not call Tilde API
        mock_tilde_client.get_data.assert_not_called()

    def test_data_error_handling(self, client, mock_tilde_client, mock_cache_service):
        """Test error handling for data requests."""
        from fastapi import HTTPException
        mock_cache_service.get.return_value = None  # Cache miss
        mock_tilde_client.get_data = AsyncMock(side_effect=HTTPException(status_code=404, detail="Not found"))

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 404
