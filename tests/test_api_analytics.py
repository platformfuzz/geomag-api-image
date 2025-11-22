"""Tests for analytics API endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_get_data_statistics_with_period(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test statistics endpoint with period parameter."""
        from unittest.mock import patch
        from app.api import analytics

        mock_cache_service.get.return_value = None  # Cache miss
        # Mock the data response structure
        mock_data = [sample_data_response]

        with patch.object(analytics.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_data

            response = client.get(
                "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "statistics" in data["data"]
            assert "query" in data["data"]
            stats = data["data"]["statistics"]
            assert "count" in stats
            assert "min" in stats
            assert "max" in stats
            assert "mean" in stats
            assert "std_dev" in stats

    def test_get_data_statistics_with_date_range(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test statistics endpoint with date range."""
        from unittest.mock import patch
        from app.api import analytics

        mock_cache_service.get.return_value = None  # Cache miss
        mock_data = [sample_data_response]

        with patch.object(analytics.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_data

            response = client.get(
                "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?"
                "start_date=2025-01-20&end_date=2025-01-21"
            )

            assert response.status_code == 200
            data = response.json()
            assert "statistics" in data["data"]
            assert data["data"]["query"]["start_date"] == "2025-01-20"
            assert data["data"]["query"]["end_date"] == "2025-01-21"

    def test_get_data_statistics_missing_params(self, client):
        """Test statistics endpoint with missing parameters."""
        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats"
        )

        assert response.status_code == 400
        assert "period" in response.json()["detail"].lower() or "start_date" in response.json()["detail"].lower()

    def test_get_data_statistics_empty_data(
        self, client, mock_tilde_client, mock_cache_service
    ):
        """Test statistics with empty data."""
        # Need to mock the analytics module's tilde_client, not the global one
        from unittest.mock import patch
        from app.api import analytics

        # Clear cache for both stats and data
        mock_cache_service.get.return_value = None
        # Return empty data list
        mock_data = [{"data": [], "series": {}, "valueUnit": "nT"}]

        with patch.object(analytics.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_data

            response = client.get(
                "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
            )

            assert response.status_code == 200
            data = response.json()
            stats = data["data"]["statistics"]
            assert stats["count"] == 0
            assert stats["min"] is None
            assert stats["max"] is None
            assert stats["mean"] is None

    def test_get_data_statistics_error_handling(
        self, client, mock_tilde_client, mock_cache_service
    ):
        """Test statistics endpoint error handling."""
        from unittest.mock import patch
        from app.api import analytics
        from fastapi import HTTPException

        # Clear cache to ensure we hit the API
        mock_cache_service.get.return_value = None

        with patch.object(analytics.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            # HTTPException should be re-raised, not converted to 500
            mock_get_data.side_effect = HTTPException(status_code=404, detail="Not found")

            response = client.get(
                "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
            )

            # The endpoint should re-raise HTTPException
            assert response.status_code == 404
            assert "Not found" in response.json()["detail"]
            # Verify the API was called (not cached)
            assert mock_get_data.called

    def test_calculate_statistics_with_no_values(
        self, client, mock_tilde_client, mock_cache_service
    ):
        """Test statistics calculation with data points that have no 'val' field."""
        from unittest.mock import patch
        from app.api import analytics

        mock_cache_service.get.return_value = None
        # Data points without 'val' field
        mock_data = [{"data": [{"time": "2025-01-20T00:00:00Z"}, {"time": "2025-01-20T01:00:00Z"}], "series": {}}]

        with patch.object(analytics.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_data

            response = client.get(
                "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
            )

            assert response.status_code == 200
            data = response.json()
            stats = data["data"]["statistics"]
            # Should return count of data points but no min/max/mean
            assert stats["count"] == 2
            assert stats["min"] is None
            assert stats["max"] is None
            assert stats["mean"] is None
