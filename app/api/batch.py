"""Batch query endpoints for multiple stations or aspects."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import asyncio
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.models.schemas import DataResponse
from app.services.cache import cache_service
from app.services.tilde_client import tilde_client

router = APIRouter(prefix="/api/v1", tags=["batch"])


class BatchQueryItem(BaseModel):
    """Single item in a batch query."""

    station: str
    name: str
    sensor_code: str
    method: str
    aspect: str


class BatchQueryRequest(BaseModel):
    """Batch query request model."""

    items: List[BatchQueryItem] = Field(..., max_length=20, description="Maximum 20 items per batch")
    period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    domain: str = "geomag"

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if len(v) > 20:
            raise ValueError("Maximum 20 items allowed per batch request")
        if len(v) == 0:
            raise ValueError("At least one item is required")
        return v


async def _fetch_item_data(
    item: BatchQueryItem,
    domain: str,
    period: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> tuple[str, dict, Optional[str]]:
    """
    Fetch data for a single batch item with caching.

    Returns:
        Tuple of (key, response_data, error_message)
    """
    key = f"{item.station}_{item.aspect}"

    # Build cache key (same format as regular data endpoints)
    if period:
        cache_key = f"data:{domain}:{item.station}:{item.name}:{item.sensor_code}:{item.method}:{item.aspect}:latest:{period}"
        is_latest = True
    else:
        cache_key = f"data:{domain}:{item.station}:{item.name}:{item.sensor_code}:{item.method}:{item.aspect}:range:{start_date}:{end_date}"
        is_latest = False

    # Check cache first
    cached = cache_service.get(cache_key, is_latest=is_latest)
    if cached:
        return (key, cached, None)

    try:
        # Fetch from API with timeout
        data = await asyncio.wait_for(
            tilde_client.get_data(
                domain=domain,
                station=item.station,
                name=item.name,
                sensor_code=item.sensor_code,
                method=item.method,
                aspect=item.aspect,
                period=period,
                start_date=start_date,
                end_date=end_date,
            ),
            timeout=30.0,  # 30 second timeout per item
        )

        # Extract data from list response
        if isinstance(data, list) and len(data) > 0:
            response_data = data[0] if isinstance(data[0], dict) else {}
        else:
            response_data = data if isinstance(data, dict) else {}

        # Cache the result
        cache_service.set(cache_key, response_data, is_latest=is_latest)

        return (key, response_data, None)
    except asyncio.TimeoutError:
        return (key, {}, f"Request timeout after 30 seconds")
    except Exception as e:
        return (key, {}, str(e))


@router.post("/data/batch", response_model=dict)
async def get_batch_data(request: BatchQueryRequest):
    """
    Get data for multiple stations/aspects in a single request.

    Useful for comparing data across stations or getting multiple aspects at once.
    Maximum 20 items per request. Requests are processed in parallel for better performance.
    """
    if not request.period and not (request.start_date and request.end_date):
        raise HTTPException(
            status_code=400,
            detail="Either 'period' (for latest) or both 'start_date' and 'end_date' (for range) must be provided",
        )

    # Process all items in parallel
    tasks = [
        _fetch_item_data(
            item=item,
            domain=request.domain,
            period=request.period,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        for item in request.items
    ]

    # Execute all requests concurrently
    results_list = await asyncio.gather(*tasks, return_exceptions=False)

    # Process results
    results = {}
    errors = {}

    for key, response_data, error in results_list:
        if error:
            errors[key] = error
        else:
            results[key] = response_data

    return {
        "results": results,
        "errors": errors,
        "total_queries": len(request.items),
        "successful": len(results),
        "failed": len(errors),
    }
