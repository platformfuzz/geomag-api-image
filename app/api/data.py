"""Data fetching endpoints."""
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models.schemas import DataResponse, DateValidator, PeriodValidator
from app.services.cache import cache_service
from app.services.tilde_client import tilde_client

router = APIRouter(prefix="/api/v1", tags=["data"])

period_validator = PeriodValidator()
date_validator = DateValidator()


@router.get(
    "/data/{station}/{name}/{sensor_code}/{method}/{aspect}/latest/{period}",
    response_model=DataResponse,
)
async def get_latest_data(
    station: str,
    name: str,
    sensor_code: str,
    method: str,
    aspect: str,
    period: str,
    domain: str = "geomag",
):
    """
    Get latest data for a specific series.

    Args:
        station: Station code (e.g., 'EYWM')
        name: Series name (e.g., 'magnetic-field-component')
        sensor_code: Sensor code (e.g., '50')
        method: Method (e.g., '60s')
        aspect: Aspect (e.g., 'X-magnetic-north')
        period: Period string (e.g., '6h', '24h', '7d')
        domain: Data domain (default: 'geomag')
    """
    # Validate period format
    try:
        period = period_validator.validate_period(period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cache_key = f"data:{domain}:{station}:{name}:{sensor_code}:{method}:{aspect}:latest:{period}"
    cached = cache_service.get(cache_key, is_latest=True)
    if cached:
        return DataResponse(data=cached)

    try:
        data = await tilde_client.get_data(
            domain=domain,
            station=station,
            name=name,
            sensor_code=sensor_code,
            method=method,
            aspect=aspect,
            period=period,
        )
        # Tilde API returns a list, wrap it in a dict for consistency
        # If it's already a dict, use it as-is
        if isinstance(data, list):
            response_data = {"items": data} if len(data) > 1 else (data[0] if len(data) == 1 else {})
        else:
            response_data = data

        # Enrich with station metadata from cached dataSummary if available
        try:
            # Use cached summary to avoid extra API call
            summary_cache_key = f"dataSummary:{domain}"
            cached_summary = cache_service.get(summary_cache_key, is_latest=False)
            if cached_summary:
                domain_info = cached_summary.get("domain", {}).get(domain, {})
                station_info = domain_info.get("stations", {}).get(station, {})
                if station_info:
                    response_data["station_metadata"] = {
                        "station": station_info.get("station"),
                        "locality": station_info.get("stationLocality"),
                        "latitude": station_info.get("latitude"),
                        "longitude": station_info.get("longitude"),
                        "elevationM": station_info.get("stationElevationM"),
                    }
        except Exception:
            # If metadata fetch fails, continue without it
            pass

        cache_service.set(cache_key, response_data, is_latest=True)
        return DataResponse(data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch data: {str(e)}"
        )


@router.get(
    "/data/{station}/{name}/{sensor_code}/{method}/{aspect}/range/{start_date}/{end_date}",
    response_model=DataResponse,
)
async def get_data_range(
    station: str,
    name: str,
    sensor_code: str,
    method: str,
    aspect: str,
    start_date: str,
    end_date: str,
    domain: str = "geomag",
):
    """
    Get data for a date range.

    Args:
        station: Station code (e.g., 'EYWM')
        name: Series name (e.g., 'magnetic-field-component')
        sensor_code: Sensor code (e.g., '50')
        method: Method (e.g., '60s')
        aspect: Aspect (e.g., 'X-magnetic-north')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        domain: Data domain (default: 'geomag')
    """
    # Validate date formats
    try:
        start_date = date_validator.validate_date(start_date)
        end_date = date_validator.validate_date(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate date range (max 90 days)
    from datetime import datetime
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    days_diff = (end_dt - start_dt).days

    if days_diff < 0:
        raise HTTPException(
            status_code=400, detail="End date must be after start date"
        )

    if days_diff > 90:
        raise HTTPException(
            status_code=400,
            detail=f"Date range cannot exceed 90 days. Requested range: {days_diff} days",
        )

    cache_key = f"data:{domain}:{station}:{name}:{sensor_code}:{method}:{aspect}:range:{start_date}:{end_date}"
    cached = cache_service.get(cache_key, is_latest=False)
    if cached:
        return DataResponse(data=cached)

    try:
        data = await tilde_client.get_data(
            domain=domain,
            station=station,
            name=name,
            sensor_code=sensor_code,
            method=method,
            aspect=aspect,
            start_date=start_date,
            end_date=end_date,
        )
        # Tilde API returns a list, wrap it in a dict for consistency
        # If it's already a dict, use it as-is
        if isinstance(data, list):
            response_data = {"items": data} if len(data) > 1 else (data[0] if len(data) == 1 else {})
        else:
            response_data = data

        # Enrich with station metadata from cached dataSummary if available
        try:
            # Use cached summary to avoid extra API call
            summary_cache_key = f"dataSummary:{domain}"
            cached_summary = cache_service.get(summary_cache_key, is_latest=False)
            if cached_summary:
                domain_info = cached_summary.get("domain", {}).get(domain, {})
                station_info = domain_info.get("stations", {}).get(station, {})
                if station_info:
                    response_data["station_metadata"] = {
                        "station": station_info.get("station"),
                        "locality": station_info.get("stationLocality"),
                        "latitude": station_info.get("latitude"),
                        "longitude": station_info.get("longitude"),
                        "elevationM": station_info.get("stationElevationM"),
                    }
        except Exception:
            # If metadata fetch fails, continue without it
            pass

        cache_service.set(cache_key, response_data, is_latest=False)
        return DataResponse(data=response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch data: {str(e)}"
        )


@router.get(
    "/data/{station}/{name}/{sensor_code}/{method}/{aspect}/day/{date}",
    response_model=DataResponse,
)
async def get_data_day(
    station: str,
    name: str,
    sensor_code: str,
    method: str,
    aspect: str,
    date: str,
    domain: str = "geomag",
):
    """
    Get data for a single day.

    Args:
        station: Station code (e.g., 'EYWM')
        name: Series name (e.g., 'magnetic-field-component')
        sensor_code: Sensor code (e.g., '50')
        method: Method (e.g., '60s')
        aspect: Aspect (e.g., 'X-magnetic-north')
        date: Date in YYYY-MM-DD format
        domain: Data domain (default: 'geomag')
    """
    # Validate date format
    try:
        date = date_validator.validate_date(date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Use range endpoint with same start and end date
    return await get_data_range(
        station=station,
        name=name,
        sensor_code=sensor_code,
        method=method,
        aspect=aspect,
        start_date=date,
        end_date=date,
        domain=domain,
    )


@router.get("/data/{station}/latest/{period}", response_model=DataResponse)
async def get_station_latest_data(
    station: str,
    period: str,
    domain: str = "geomag",
    name: str = "magnetic-field-component",
    sensor_code: str = "50",
    method: str = "60s",
    aspect: str = "X-magnetic-north",
):
    """
    Convenience endpoint to get latest data for a station with common defaults.

    Uses default values for common series (magnetic-field-component, sensor 50, 60s method, X-magnetic-north).
    You can override these via query parameters.

    Args:
        station: Station code (e.g., 'EYWM')
        period: Period string (e.g., '6h', '24h', '7d')
        domain: Data domain (default: 'geomag')
        name: Series name (default: 'magnetic-field-component')
        sensor_code: Sensor code (default: '50')
        method: Method (default: '60s')
        aspect: Aspect (default: 'X-magnetic-north')
    """
    return await get_latest_data(
        station=station,
        name=name,
        sensor_code=sensor_code,
        method=method,
        aspect=aspect,
        period=period,
        domain=domain,
    )
