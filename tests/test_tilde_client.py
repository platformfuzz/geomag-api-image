"""Tests for Tilde client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.tilde_client import TildeClient


class TestTildeClient:
    """Tests for TildeClient."""

    @pytest.fixture
    def client(self):
        """Create a TildeClient instance."""
        return TildeClient(base_url="https://test.example.com/v4", timeout=10)

    def test_client_initialization(self):
        """Test client initialization."""
        client = TildeClient(base_url="https://test.com", timeout=30)
        assert client.base_url == "https://test.com"
        assert client.timeout == 30

    def test_build_url(self, client):
        """Test URL building."""
        url = client._build_url("data", "geomag", "EYWM")
        assert url == "https://test.example.com/v4/data/geomag/EYWM"

        url = client._build_url("dataSummary", "geomag")
        assert url == "https://test.example.com/v4/dataSummary/geomag"

    @pytest.mark.asyncio
    async def test_get_data_summary_success(self, client):
        """Test successful data summary request."""
        mock_response_data = {"EYWM": {"test": "data"}}

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await client.get_data_summary(domain="geomag")

            assert result == mock_response_data
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"
            assert "dataSummary/geomag" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_data_summary_with_station(self, client):
        """Test data summary request (station parameter is ignored, Tilde doesn't support it)."""
        mock_response_data = {"test": "data"}

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await client.get_data_summary(domain="geomag", station="EYWM")

            assert result == mock_response_data
            call_args = mock_request.call_args
            # Should only call with domain, not station (Tilde v4 doesn't support station-specific endpoint)
            assert "dataSummary/geomag" in call_args[0][1]
            assert "dataSummary/geomag/EYWM" not in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_data_latest(self, client):
        """Test getting latest data."""
        mock_response_data = {"data": []}

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await client.get_data(
                domain="geomag",
                station="EYWM",
                name="magnetic-field-component",
                sensor_code="50",
                method="60s",
                aspect="X-magnetic-north",
                period="6h"
            )

            assert result == mock_response_data
            call_args = mock_request.call_args
            assert "data/geomag/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_data_range(self, client):
        """Test getting data for date range."""
        mock_response_data = {"data": []}

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_request.return_value = mock_response

            result = await client.get_data(
                domain="geomag",
                station="EYWM",
                name="magnetic-field-component",
                sensor_code="50",
                method="60s",
                aspect="X-magnetic-north",
                start_date="2025-01-20",
                end_date="2025-01-21"
            )

            assert result == mock_response_data
            call_args = mock_request.call_args
            assert "data/geomag/EYWM/magnetic-field-component/50/60s/X-magnetic-north/2025-01-20/2025-01-21" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_get_data_missing_params(self, client):
        """Test that missing parameters raise HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            await client.get_data(
                domain="geomag",
                station="EYWM",
                name="test",
                sensor_code="50",
                method="60s",
                aspect="X"
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_data_404_error(self, client):
        """Test handling of 404 errors."""
        from httpx import HTTPStatusError

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": "Not found"}
            mock_response.text = "Not found"

            mock_error = HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
            mock_response.raise_for_status.side_effect = mock_error
            mock_request.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                await client.get_data(
                    domain="geomag",
                    station="INVALID",
                    name="test",
                    sensor_code="50",
                    method="60s",
                    aspect="X",
                    period="6h"
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_data_400_error(self, client):
        """Test handling of 400 errors."""
        from httpx import HTTPStatusError

        with patch.object(client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}
            mock_response.text = "Bad request"

            mock_error = HTTPStatusError("Bad request", request=MagicMock(), response=mock_response)
            mock_response.raise_for_status.side_effect = mock_error
            mock_request.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                await client.get_data(
                    domain="geomag",
                    station="EYWM",
                    name="test",
                    sensor_code="50",
                    method="60s",
                    aspect="X",
                    period="6h"
                )

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing the client."""
        await client.close()
        # Should not raise any exceptions
