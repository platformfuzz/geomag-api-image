"""Pytest configuration and fixtures."""
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.services.cache import CacheService
from app.services.tilde_client import TildeClient


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_tilde_client(monkeypatch):
    """Create a mock TildeClient."""
    mock_client = AsyncMock(spec=TildeClient)
    # Patch tilde_client in all modules that use it
    monkeypatch.setattr("app.api.discovery.tilde_client", mock_client)
    monkeypatch.setattr("app.api.data.tilde_client", mock_client)
    monkeypatch.setattr("app.api.analytics.tilde_client", mock_client)
    monkeypatch.setattr("app.api.batch.tilde_client", mock_client)
    return mock_client


@pytest.fixture
def mock_cache_service(monkeypatch):
    """Create a mock CacheService."""
    mock_cache = MagicMock(spec=CacheService)
    mock_cache.get.return_value = None
    mock_cache.set.return_value = None
    # Patch cache_service in all modules that use it
    monkeypatch.setattr("app.api.discovery.cache_service", mock_cache)
    monkeypatch.setattr("app.api.data.cache_service", mock_cache)
    monkeypatch.setattr("app.api.analytics.cache_service", mock_cache)
    monkeypatch.setattr("app.api.batch.cache_service", mock_cache)
    return mock_cache


@pytest.fixture
def sample_data_summary():
    """Sample data summary response from Tilde API (matches actual Tilde v4 structure)."""
    return {
        "domain": {
            "geomag": {
                "domain": "geomag",
                "description": "Geomagnetic Sensors",
                "stations": {
                    "EYWM": {
                        "station": "EYWM",
                        "stationLocality": "West Melton Geomagnetic Observatory",
                        "latitude": -43.474,
                        "longitude": 172.3928,
                        "stationElevationM": 87,
                        "sensorCodes": {
                            "50": {
                                "sensorCode": "50",
                                "names": {
                                    "magnetic-field-component": {
                                        "name": "magnetic-field-component",
                                        "methods": {
                                            "60s": {
                                                "method": "60s",
                                                "aspects": [
                                                    "X-magnetic-north",
                                                    "Y-magnetic-east",
                                                    "Z-vertical",
                                                ]
                                            }
                                        }
                                    },
                                    "magnetic-field": {
                                        "name": "magnetic-field",
                                        "methods": {
                                            "60s": {
                                                "method": "60s",
                                                "aspects": ["F-total-field"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "TEST": {
                        "station": "TEST",
                        "stationLocality": "Test Station",
                        "latitude": -40.0,
                        "longitude": 175.0,
                        "stationElevationM": 100,
                        "sensorCodes": {
                            "50": {
                                "sensorCode": "50",
                                "names": {
                                    "magnetic-field-component": {
                                        "name": "magnetic-field-component",
                                        "methods": {
                                            "60s": {
                                                "method": "60s",
                                                "aspects": ["X-magnetic-north"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_data_response():
    """Sample data response from Tilde API."""
    return {
        "metadata": {
            "station": "EYWM",
            "name": "magnetic-field-component",
            "sensorCode": "50",
            "method": "60s",
            "aspect": "X-magnetic-north"
        },
        "data": [
            {
                "timestamp": "2025-01-20T12:00:00Z",
                "value": 12345.67
            },
            {
                "timestamp": "2025-01-20T12:01:00Z",
                "value": 12346.12
            }
        ]
    }
