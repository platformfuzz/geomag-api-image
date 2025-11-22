# geomag-api-image

Containerized REST API service for fetching and serving GeoNet geomagnetic data from Tilde v4.

## Overview

This FastAPI-based service provides comprehensive access to GeoNet's Tilde v4 geomagnetic data API with:

- Data discovery endpoints to explore available stations and series
- Flexible data fetching endpoints supporting latest data and date ranges
- Statistics and analytics endpoints for data analysis
- Batch query endpoints for efficient multi-station/aspect queries
- Built-in caching to reduce upstream API calls
- Automatic OpenAPI documentation
- Health check endpoints

## Quick Start

### Build the Image

```bash
./scripts/build.sh
```

Or manually:

```bash
docker build -t geomag-api-image:latest .
```

### Run the Container

```bash
docker run -p 8000:8000 geomag-api-image:latest
```

The API will be available at `http://localhost:8000`

### Access Documentation

- Interactive API docs: <http://localhost:8000/docs>
- OpenAPI schema: <http://localhost:8000/openapi.json>

## API Endpoints

### Discovery Endpoints

**Get all data summaries:**

```bash
curl http://localhost:8000/api/v1/dataSummary
```

**Get data summary for a specific station:**

```bash
curl http://localhost:8000/api/v1/dataSummary/EYWM
```

**List all available stations:**

```bash
curl http://localhost:8000/api/v1/stations
```

### Data Fetching Endpoints

**Get latest 6 hours of data:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h"
```

**Get data for a date range:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21"
```

**Get data for a single day:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21"
```

**Convenience endpoint with defaults:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/latest/6h"
```

### Analytics Endpoints

**Get statistics (min, max, mean, std dev) for latest data:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h"
```

**Get statistics for a date range:**

```bash
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21"
```

### Batch Query Endpoints

**Query multiple stations/aspects in a single request:**

```bash
curl -X POST http://localhost:8000/api/v1/data/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "X-magnetic-north"
      },
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "Y-magnetic-east"
      }
    ],
    "period": "6h"
  }'
```

**Batch query with date range:**

```bash
curl -X POST http://localhost:8000/api/v1/data/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "X-magnetic-north"
      }
    ],
    "start_date": "2025-01-20",
    "end_date": "2025-01-21"
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Configuration

The service can be configured via environment variables:

- `TILDE_BASE_URL` - Tilde API base URL (default: `https://tilde.geonet.org.nz/v4`)
- `CACHE_TTL_LATEST` - Cache TTL for latest data in seconds (default: 300)
- `CACHE_TTL_HISTORICAL` - Cache TTL for historical data in seconds (default: 3600)
- `API_PORT` - Server port (default: 8000)

Example:

```bash
docker run -p 8000:8000 \
  -e CACHE_TTL_LATEST=600 \
  -e CACHE_TTL_HISTORICAL=7200 \
  geomag-api-image:latest
```

## Example Usage

### Discover Available Data

First, explore what's available:

```bash
# Get all stations
curl http://localhost:8000/api/v1/stations | jq .

# Get details for a specific station
curl http://localhost:8000/api/v1/dataSummary/EYWM | jq .
```

### Fetch Magnetic Field Data

```bash
# Latest 6 hours, X component (magnetic north)
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/latest/6h" | jq .

# Latest 6 hours, total field (F)
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field/50/60s/F-total-field/latest/6h" | jq .

# Entire UTC day for 2025-11-21 (using day endpoint)
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/day/2025-11-21" | jq .

# Or using range endpoint for the same day
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/range/2025-11-21/2025-11-21" | jq .
```

### Get Statistics

```bash
# Get statistics for latest 6 hours
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?period=6h" | jq .

# Get statistics for a date range
curl "http://localhost:8000/api/v1/data/EYWM/magnetic-field-component/50/60s/X-magnetic-north/stats?start_date=2025-01-20&end_date=2025-01-21" | jq .
```

### Batch Queries

```bash
# Query multiple aspects at once
curl -X POST http://localhost:8000/api/v1/data/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "X-magnetic-north"
      },
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "Y-magnetic-east"
      },
      {
        "station": "EYWM",
        "name": "magnetic-field-component",
        "sensor_code": "50",
        "method": "60s",
        "aspect": "Z-vertical"
      }
    ],
    "period": "6h"
  }' | jq .
```

## Tilde v4 API Reference

This service wraps GeoNet's Tilde v4 API. For more information:

- [Tilde v4 Documentation](https://tilde.geonet.org.nz)
- [Geomag Dashboard](https://www.geonet.org.nz/data/types/geomag)

## Development

### Local Development

```bash
# Create a virtual environment (recommended)
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Make sure you're in the virtual environment (see Local Development above)
# Install dependencies if not already installed
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_data.py

# Run tests in verbose mode
pytest -v

# Run README example tests (verifies all examples work)
pytest tests/test_readme_examples.py -v
```

The test suite includes:

- Unit tests for models and validators
- Service tests for cache and Tilde client
- API endpoint tests for discovery, data, analytics, and batch endpoints
- Integration tests for the main application
- **README example tests** - Verifies all examples in this README actually work

Current test coverage: **84%**

> **Note:** All examples in this README are automatically tested. If an example fails, the tests will catch it, ensuring the documentation stays accurate.

### Project Structure

```plaintext
app/
├── main.py              # FastAPI application entry point
├── api/
│   ├── discovery.py    # Discovery endpoints
│   ├── data.py         # Data fetching endpoints
│   ├── analytics.py    # Statistics and analytics endpoints
│   └── batch.py        # Batch query endpoints
├── models/
│   └── schemas.py      # Pydantic models
└── services/
    ├── tilde_client.py # Tilde v4 API client
    └── cache.py        # Caching service
tests/
├── conftest.py         # Pytest fixtures and configuration
├── test_models.py      # Tests for models and validators
├── test_cache.py       # Tests for cache service
├── test_tilde_client.py # Tests for Tilde client
├── test_api_discovery.py # Tests for discovery endpoints
├── test_api_data.py    # Tests for data endpoints
├── test_api_analytics.py # Tests for analytics endpoints
├── test_api_batch.py   # Tests for batch endpoints
├── test_readme_examples.py # Tests for all README examples
└── test_main.py        # Tests for main application
```

## License

See LICENSE file for details.
