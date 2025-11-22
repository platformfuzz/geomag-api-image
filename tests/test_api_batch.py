"""Tests for batch API endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestBatchEndpoints:
    """Tests for batch endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_batch_query_success(
        self, client, mock_tilde_client, sample_data_response
    ):
        """Test successful batch query."""
        from unittest.mock import patch
        from app.api import batch

        mock_data = [sample_data_response]

        with patch.object(batch.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_data

            request_data = {
                "items": [
                    {
                        "station": "EYWM",
                        "name": "magnetic-field-component",
                        "sensor_code": "50",
                        "method": "60s",
                        "aspect": "X-magnetic-north",
                    },
                    {
                        "station": "EYWM",
                        "name": "magnetic-field-component",
                        "sensor_code": "50",
                        "method": "60s",
                        "aspect": "Y-magnetic-east",
                    },
                ],
                "period": "6h",
            }

            response = client.post("/api/v1/data/batch", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "errors" in data
            assert data["total_queries"] == 2
            assert data["successful"] == 2
            assert data["failed"] == 0
            assert "EYWM_X-magnetic-north" in data["results"]
            assert "EYWM_Y-magnetic-east" in data["results"]

    def test_batch_query_with_date_range(
        self, client, mock_tilde_client, sample_data_response
    ):
        """Test batch query with date range."""
        mock_data = [sample_data_response]
        mock_tilde_client.get_data = AsyncMock(return_value=mock_data)

        request_data = {
            "items": [
                {
                    "station": "EYWM",
                    "name": "magnetic-field-component",
                    "sensor_code": "50",
                    "method": "60s",
                    "aspect": "X-magnetic-north",
                }
            ],
            "start_date": "2025-01-20",
            "end_date": "2025-01-21",
        }

        response = client.post("/api/v1/data/batch", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 1

    def test_batch_query_missing_params(self, client):
        """Test batch query with missing parameters."""
        request_data = {
            "items": [
                {
                    "station": "EYWM",
                    "name": "magnetic-field-component",
                    "sensor_code": "50",
                    "method": "60s",
                    "aspect": "X-magnetic-north",
                }
            ]
        }

        response = client.post("/api/v1/data/batch", json=request_data)

        assert response.status_code == 400
        assert "period" in response.json()["detail"].lower() or "start_date" in response.json()["detail"].lower()

    def test_batch_query_with_errors(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test batch query with some errors."""
        from unittest.mock import patch
        from app.api import batch
        from fastapi import HTTPException

        # Clear cache to ensure we hit the API
        mock_cache_service.get.return_value = None

        with patch.object(batch.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            # First call succeeds, second fails
            mock_get_data.side_effect = [
                [sample_data_response],
                HTTPException(status_code=404, detail="Not found"),
            ]

            request_data = {
                "items": [
                    {
                        "station": "EYWM",
                        "name": "magnetic-field-component",
                        "sensor_code": "50",
                        "method": "60s",
                        "aspect": "X-magnetic-north",
                    },
                    {
                        "station": "INVALID",
                        "name": "magnetic-field-component",
                        "sensor_code": "50",
                        "method": "60s",
                        "aspect": "X-magnetic-north",
                    },
                ],
                "period": "6h",
            }

            response = client.post("/api/v1/data/batch", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["total_queries"] == 2
            assert data["successful"] == 1
            assert data["failed"] == 1
            assert len(data["errors"]) == 1
            # Verify the API was called (not cached)
            assert mock_get_data.call_count == 2
