"""Discovery endpoints for exploring available data."""
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models.schemas import DataSummaryResponse, StationListResponse
from app.services.cache import cache_service
from app.services.tilde_client import tilde_client

router = APIRouter(prefix="/api/v1", tags=["discovery"])


@router.get("/dataSummary", response_model=DataSummaryResponse)
async def get_data_summary(domain: str = "geomag"):
    """
    Get data summary for all stations in the specified domain.

    Returns information about available stations, series, sensors, methods, and aspects.
    """
    cache_key = f"dataSummary:{domain}"
    cached = cache_service.get(cache_key, is_latest=False)
    if cached:
        return DataSummaryResponse(data=cached)

    try:
        data = await tilde_client.get_data_summary(domain=domain)
        cache_service.set(cache_key, data, is_latest=False)
        return DataSummaryResponse(data=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch data summary: {str(e)}"
        )


@router.get("/dataSummary/{station}", response_model=DataSummaryResponse)
async def get_station_data_summary(station: str, domain: str = "geomag"):
    """
    Get data summary for a specific station.

    Returns information about available series, sensors, methods, and aspects for the station.

    Note: Tilde v4 doesn't support station-specific dataSummary endpoints, so this
    filters the domain summary to return only data for the specified station.
    """
    cache_key = f"dataSummary:{domain}:{station}"
    cached = cache_service.get(cache_key, is_latest=False)
    if cached:
        return DataSummaryResponse(data=cached)

    try:
        # Get full domain summary (Tilde v4 doesn't support station-specific endpoint)
        domain_data = await tilde_client.get_data_summary(domain=domain)

        # Extract station data from the nested structure
        # Structure: domain -> {domain_name} -> stations -> {station_code}
        domain_info = domain_data.get("domain", {}).get(domain, {})
        stations = domain_info.get("stations", {})

        if station not in stations:
            raise HTTPException(
                status_code=404,
                detail=f"Station '{station}' not found in domain '{domain}'",
            )

        # Return station-specific data
        station_data = {
            "station": stations[station],
            "domain": domain,
            "station_code": station
        }

        cache_service.set(cache_key, station_data, is_latest=False)
        return DataSummaryResponse(data=station_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch station data summary: {str(e)}",
        )


@router.get("/stations", response_model=StationListResponse)
async def get_stations(domain: str = "geomag"):
    """
    Get list of all available stations in the specified domain.
    """
    cache_key = f"stations:{domain}"
    cached = cache_service.get(cache_key, is_latest=False)
    if cached:
        return StationListResponse(stations=cached)

    try:
        data = await tilde_client.get_data_summary(domain=domain)
        # Extract station codes from the nested structure
        # Structure: domain -> {domain_name} -> stations -> {station_code}
        domain_info = data.get("domain", {}).get(domain, {})
        stations_dict = domain_info.get("stations", {})
        stations = list(stations_dict.keys()) if isinstance(stations_dict, dict) else []
        cache_service.set(cache_key, stations, is_latest=False)
        return StationListResponse(stations=stations)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch stations: {str(e)}"
        )
