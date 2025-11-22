"""HTTP client for Tilde v4 API."""
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException


class TildeClient:
    """Client for interacting with GeoNet's Tilde v4 API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize Tilde client.

        Args:
            base_url: Base URL for Tilde API (defaults to env var or production URL)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv(
            "TILDE_BASE_URL", "https://tilde.geonet.org.nz/v4"
        )
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _build_url(self, *path_parts: str) -> str:
        """Build URL from base URL and path parts."""
        path = "/".join(str(part) for part in path_parts if part)
        # Ensure no double slashes
        path = path.replace("//", "/")
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url.rstrip('/')}{path}"

    async def _request(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request and handle errors.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response as dict

        Raises:
            HTTPException: For HTTP errors
        """
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"detail": e.response.text or str(e)}

            if status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Resource not found: {error_detail.get('detail', 'Unknown error')}",
                )
            elif status_code == 400:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bad request: {error_detail.get('detail', 'Invalid parameters')}",
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Upstream API error ({status_code}): {error_detail.get('detail', 'Unknown error')}",
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, detail="Request to Tilde API timed out"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, detail=f"Failed to connect to Tilde API: {str(e)}"
            )

    async def get_data_summary(
        self, domain: str = "geomag", station: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get data summary from Tilde API.

        Args:
            domain: Data domain (default: 'geomag')
            station: Optional station code (not used - Tilde v4 doesn't support station-specific endpoints)

        Returns:
            Data summary response
        """
        # Note: Tilde v4 only supports /v4/dataSummary/{domain}
        # Station filtering must be done client-side
        url = self._build_url("dataSummary", domain)
        return await self._request("GET", url)

    async def get_data(
        self,
        domain: str,
        station: str,
        name: str,
        sensor_code: str,
        method: str,
        aspect: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get data from Tilde API.

        Args:
            domain: Data domain (e.g., 'geomag')
            station: Station code (e.g., 'EYWM')
            name: Series name (e.g., 'magnetic-field-component')
            sensor_code: Sensor code (e.g., '50')
            method: Method (e.g., '60s')
            aspect: Aspect (e.g., 'X-magnetic-north')
            start_date: Start date in YYYY-MM-DD format (for date range)
            end_date: End date in YYYY-MM-DD format (for date range)
            period: Period string like '6h' (for latest data)

        Returns:
            Data response

        Raises:
            HTTPException: If parameters are invalid
        """
        if period:
            # Latest data: /v4/data/{domain}/{station}/{name}/{sensorCode}/{method}/{aspect}/latest/{period}
            url = self._build_url(
                "data",
                domain,
                station,
                name,
                sensor_code,
                method,
                aspect,
                "latest",
                period,
            )
        elif start_date and end_date:
            # Date range: /v4/data/{domain}/{station}/{name}/{sensorCode}/{method}/{aspect}/{startDate}/{endDate}
            url = self._build_url(
                "data",
                domain,
                station,
                name,
                sensor_code,
                method,
                aspect,
                start_date,
                end_date,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'period' (for latest) or both 'start_date' and 'end_date' (for range) must be provided",
            )

        return await self._request("GET", url)


# Global client instance
tilde_client = TildeClient()
