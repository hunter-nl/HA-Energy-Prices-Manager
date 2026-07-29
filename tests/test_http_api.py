"""Tests for price-period validation."""

from custom_components.energy_prices_manager.http_api import _validate_periods


def test_validate_periods_sorts_valid_periods() -> None:
    """Valid periods are normalized and sorted by start date."""
    periods, errors = _validate_periods(
        [
            {"start": "2026-07-01", "end": "2026-07-31", "t1": 0.2, "t2": 0.3, "gas": 1.1},
            {"start": "2026-01-01", "end": "2026-06-30", "t1": 0.1, "t2": 0.2, "gas": 1.0},
        ]
    )

    assert errors == []
    assert [period["start"] for period in periods] == ["2026-01-01", "2026-07-01"]


def test_validate_periods_rejects_invalid_payloads() -> None:
    """Invalid dates, values, and overlapping periods are rejected."""
    periods, errors = _validate_periods(
        [
            {"start": "2026-01-01", "end": "2026-01-31", "t1": 0.2, "t2": 0.3, "gas": 1.1},
            {"start": "2026-01-31", "end": "2026-02-28", "t1": True, "t2": 0.3, "gas": 1.1},
            {"start": "not-a-date", "end": "2026-02-28", "t1": 0.2, "t2": 0.3, "gas": 1.1},
        ]
    )

    assert periods == [{"start": "2026-01-01", "end": "2026-01-31", "t1": 0.2, "t2": 0.3, "gas": 1.1}]
    assert len(errors) == 2


def test_validate_periods_rejects_overlapping_periods() -> None:
    """Adjacent periods may not share a date."""
    _, errors = _validate_periods(
        [
            {"start": "2026-01-01", "end": "2026-01-31", "t1": 0.2, "t2": 0.3, "gas": 1.1},
            {"start": "2026-01-31", "end": "2026-02-28", "t1": 0.2, "t2": 0.3, "gas": 1.1},
        ]
    )

    assert len(errors) == 1
    assert "overlap" in errors[0]
