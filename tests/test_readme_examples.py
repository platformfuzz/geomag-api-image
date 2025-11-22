"""Integration tests for README examples.

These tests verify that all examples in the README actually work.
This ensures the documentation stays in sync with the implementation.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestReadmeExamples:
    """Test all examples from README.md to ensure they work."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_tilde_client(self, monkeypatch):
        """Mock Tilde client for all modules."""
        from app.services.tilde_client import TildeClient

        mock_client = AsyncMock(spec=TildeClient)
        monkeypatch.setattr("app.api.discovery.tilde_client", mock_client)
        monkeypatch.setattr("app.api.data.tilde_client", mock_client)
        monkeypatch.setattr("app.api.analytics.tilde_client", mock_client)
        monkeypatch.setattr("app.api.batch.tilde_client", mock_client)
        return mock_client

    @pytest.fixture
    def mock_cache_service(self, monkeypatch):
        """Mock cache service for all modules."""
        from app.services.cache import CacheService

        mock_cache = MagicMock(spec=CacheService)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        monkeypatch.setattr("app.api.discovery.cache_service", mock_cache)
        monkeypatch.setattr("app.api.data.cache_service", mock_cache)
        monkeypatch.setattr("app.api.analytics.cache_service", mock_cache)
        monkeypatch.setattr("app.api.batch.cache_service", mock_cache)
        return mock_cache

    @pytest.fixture
    def sample_data_response(self):
        """Sample data response matching Tilde API format."""
        return {
            "data": [
                {"time": "2025-01-20T00:00:00Z", "val": 12345.67},
                {"time": "2025-01-20T01:00:00Z", "val": 12346.12},
            ],
            "series": {
                "station": "EYWM",
                "name": "magnetic-field-component",
                "sensorCode": "50",
                "method": "60s",
                "aspect": "X-magnetic-north",
            },
            "valueUnit": "nT",
        }

    def test_discovery_get_all_data_summaries(
        self, client, mock_tilde_client, mock_cache_service, sample_data_summary
    ):
        """Test: GET /api/v1/dataSummary"""
        # Example: curl http://localhost:8000/api/v1/dataSummary
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary")

        assert response.status_code == 200
        assert "data" in response.json()

    def test_discovery_get_station_data_summary(
        self, client, mock_tilde_client, mock_cache_service, sample_data_summary
    ):
        """Test: GET /api/v1/dataSummary/EYWM"""
        # Example: curl http://localhost:8000/api/v1/dataSummary/EYWM
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary/EYWM")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["station_code"] == "EYWM"

    def test_discovery_list_stations(
        self, client, mock_tilde_client, mock_cache_service, sample_data_summary
    ):
        """Test: GET /api/v1/stations"""
        # Example: curl http://localhost:8000/api/v1/stations
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/stations")

        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)
        assert "EYWM" in data["stations"]

    def test_data_get_latest_6h(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/EYWM/.../latest/6h"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_data_get_date_range(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/.../range/2025-11-21/2025-11-21"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_data_get_single_day(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/.../day/2025-11-21"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_data_convenience_endpoint(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/EYWM/latest/6h"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/latest/6h"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get("/api/v1/data/EYWM/latest/6h")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_analytics_stats_with_period(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/.../stats?period=6h"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "statistics" in data["data"]
        assert "count" in data["data"]["statistics"]

    def test_analytics_stats_with_date_range(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: GET /api/v1/data/.../stats?start_date=2025-01-20&end_date=2025-01-21"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21"
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data["data"]

    def test_batch_query_multiple_aspects(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: POST /api/v1/data/batch with multiple aspects"""
        # Example from README: batch query with X, Y, Z components
        from unittest.mock import patch
        from app.api import batch

        with patch.object(batch.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = [sample_data_response]

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
                    {
                        "station": "EYWM",
                        "name": "magnetic-field-component",
                        "sensor_code": "50",
                        "method": "60s",
                        "aspect": "Z-vertical",
                    },
                ],
                "period": "6h",
            }

            response = client.post("/api/v1/data/batch", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "errors" in data
            assert data["total_queries"] == 3
            assert data["successful"] == 3

    def test_batch_query_with_date_range(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test: POST /api/v1/data/batch with date range"""
        # Example from README: batch query with date range
        from unittest.mock import patch
        from app.api import batch

        with patch.object(batch.tilde_client, "get_data", new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = [sample_data_response]

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

    def test_health_check(self, client):
        """Test: GET /health"""
        # Example: curl http://localhost:8000/health
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "geomag-api"

    def test_root_endpoint(self, client):
        """Test: GET /"""
        # Example: Access root endpoint
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "docs" in data

    def test_example_usage_discover_stations(
        self, client, mock_tilde_client, mock_cache_service, sample_data_summary
    ):
        """Test README example: Discover Available Data - Get all stations"""
        # Example: curl http://localhost:8000/api/v1/stations | jq .
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/stations")

        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)

    def test_example_usage_get_station_details(
        self, client, mock_tilde_client, mock_cache_service, sample_data_summary
    ):
        """Test README example: Discover Available Data - Get details for specific station"""
        # Example: curl http://localhost:8000/api/v1/dataSummary/EYWM | jq .
        mock_tilde_client.get_data_summary = AsyncMock(return_value=sample_data_summary)

        response = client.get("/api/v1/dataSummary/EYWM")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_example_usage_latest_x_component(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Latest 6 hours, X component"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_example_usage_latest_total_field(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Latest 6 hours, total field (F)"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field/50/60s/F-total-field/latest/6h" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field/50/60s/F-total-field/latest/6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_example_usage_day_endpoint(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Entire UTC day using day endpoint"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_example_usage_range_endpoint(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Using range endpoint for same day"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_example_usage_stats_latest(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Get statistics for latest 6 hours"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data["data"]
        assert "min" in data["data"]["statistics"]
        assert "max" in data["data"]["statistics"]
        assert "mean" in data["data"]["statistics"]

    def test_example_usage_stats_date_range(
        self, client, mock_tilde_client, mock_cache_service, sample_data_response
    ):
        """Test README example: Get statistics for date range"""
        # Example: curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21" | jq .
        mock_tilde_client.get_data = AsyncMock(return_value=[sample_data_response])

        response = client.get(
            "/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21"
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data["data"]
