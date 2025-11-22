"""Tests for Pydantic models and validators."""
import pytest

from app.models.schemas import DateValidator, PeriodValidator


class TestPeriodValidator:
    """Tests for PeriodValidator."""

    def test_valid_periods(self):
        """Test valid period formats."""
        validator = PeriodValidator()
        assert validator.validate_period("6h") == "6h"
        assert validator.validate_period("24h") == "24h"
        assert validator.validate_period("7d") == "7d"
        assert validator.validate_period("30m") == "30m"
        assert validator.validate_period("120s") == "120s"

    def test_invalid_periods(self):
        """Test invalid period formats."""
        validator = PeriodValidator()

        with pytest.raises(ValueError, match="cannot be empty"):
            validator.validate_period("")

        with pytest.raises(ValueError, match="format"):
            validator.validate_period("6")

        with pytest.raises(ValueError, match="format"):
            validator.validate_period("hours")

        with pytest.raises(ValueError, match="format"):
            validator.validate_period("6 hours")

        with pytest.raises(ValueError, match="format"):
            validator.validate_period("abc")


class TestDateValidator:
    """Tests for DateValidator."""

    def test_valid_dates(self):
        """Test valid date formats."""
        validator = DateValidator()
        assert validator.validate_date("2025-01-20") == "2025-01-20"
        assert validator.validate_date("2024-12-31") == "2024-12-31"
        assert validator.validate_date("2023-02-28") == "2023-02-28"

    def test_invalid_dates(self):
        """Test invalid date formats."""
        validator = DateValidator()

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validator.validate_date("2025/01/20")

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validator.validate_date("01-20-2025")

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validator.validate_date("2025-1-20")

        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            validator.validate_date("invalid")

        with pytest.raises(ValueError):
            validator.validate_date("2025-13-01")  # Invalid month

        with pytest.raises(ValueError):
            validator.validate_date("2025-02-30")  # Invalid day
