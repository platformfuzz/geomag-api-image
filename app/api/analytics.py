"""Analytics and statistics endpoints for geomagnetic data."""
import statistics
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import DataResponse
from app.services.cache import cache_service
from app.services.tilde_client import tilde_client

router = APIRouter(prefix="/api/v1", tags=["analytics"])


def calculate_statistics(data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics from data points."""
    if not data_points:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "std_dev": None,
        }

    values = [float(point.get("val", 0)) for point in data_points if "val" in point]

    if not values:
        return {
            "count": len(data_points),
            "min": None,
            "max": None,
            "mean": None,
            "std_dev": None,
        }

    stats = {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }

    return stats


@router.get("/data/{station}/{name}/{sensor_code}/{method}/{aspect}/stats", response_model=DataResponse)
async def get_data_statistics(
    station: str,
    name: str,
    sensor_code: str,
    method: str,
    aspect: str,
    period: Optional[str] = Query(None, description="Period for latest data (e.g., '6h', '24h')"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    domain: str = "geomag",
):
    """
    Get statistics (min, max, mean, std dev) for a data series.

    Requires either 'period' (for latest data) or both 'start_date' and 'end_date' (for range).
    """
    if not period and not (start_date and end_date):
        raise HTTPException(
            status_code=400,
            detail="Either 'period' (for latest) or both 'start_date' and 'end_date' (for range) must be provided",
        )

    # Build cache key for statistics
    cache_key_parts = [
        "stats",
        domain,
        station,
        name,
        sensor_code,
        method,
        aspect,
    ]
    if period:
        cache_key_parts.append(f"period:{period}")
    else:
        cache_key_parts.append(f"range:{start_date}:{end_date}")
    cache_key = ":".join(cache_key_parts)

    # Check cache first (statistics are cached longer than raw data)
    cached_stats = cache_service.get(cache_key, is_latest=False)
    if cached_stats:
        return DataResponse(data=cached_stats)

    try:
        # Fetch data from Tilde
        data = await tilde_client.get_data(
            domain=domain,
            station=station,
            name=name,
            sensor_code=sensor_code,
            method=method,
            aspect=aspect,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )

        # Extract data points
        if isinstance(data, list) and len(data) > 0:
            data_dict = data[0] if isinstance(data[0], dict) else {}
        else:
            data_dict = data if isinstance(data, dict) else {}

        data_points = data_dict.get("data", [])

        # Calculate statistics
        stats = calculate_statistics(data_points)

        # Return enriched response
        response_data = {
            **data_dict,
            "statistics": stats,
            "query": {
                "station": station,
                "name": name,
                "sensor_code": sensor_code,
                "method": method,
                "aspect": aspect,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
            },
        }

        # Cache statistics result (use historical cache with longer TTL)
        cache_service.set(cache_key, response_data, is_latest=False)

        return DataResponse(data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate statistics: {str(e)}"
        )
