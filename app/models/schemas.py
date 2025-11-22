"""Pydantic models for request/response validation."""
from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DataSummaryResponse(BaseModel):
    """Response model for dataSummary endpoint."""

    data: Dict[str, Any]


class StationListResponse(BaseModel):
    """Response model for stations list endpoint."""

    stations: List[str]


class DataResponse(BaseModel):
    """Response model for data endpoints."""

    data: Any  # Can be dict or list - Tilde API returns list for data endpoints


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    service: str


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: str
    detail: Optional[str] = None


class PeriodValidator:
    """Validator for period strings like '6h', '24h', '7d'."""

    @staticmethod
    def validate_period(period: str) -> str:
        """Validate period format."""
        if not period:
            raise ValueError("Period cannot be empty")
        # Period should be a number followed by a unit (h, d, m, s)
        import re

        pattern = r"^\d+[hdms]$"
        if not re.match(pattern, period):
            raise ValueError(
                "Period must be in format '<number><unit>' where unit is h, d, m, or s"
            )
        return period


class DateValidator:
    """Validator for date strings in YYYY-MM-DD format."""

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date format YYYY-MM-DD."""
        try:
            date.fromisoformat(date_str)
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return date_str
