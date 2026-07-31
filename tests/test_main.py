"""Tests for the Energy Prices Manager App."""

from datetime import date

import pytest

from app.main import Period, _current_period, _validate_periods


def test_current_period_selects_active_range() -> None:
    """The app selects the period containing the requested date."""
    periods = _validate_periods(
        [
            Period(start=date(2026, 1, 1), end=date(2026, 6, 30), t1=0.2, t2=0.3, gas=1.1),
            Period(start=date(2026, 7, 1), end=date(2026, 12, 31), t1=0.1, t2=0.25, gas=1.0),
        ]
    )

    assert _current_period(periods, date(2026, 7, 1)) == periods[1]


def test_periods_must_not_overlap() -> None:
    """Adjacent periods cannot share a date."""
    periods = [
        Period(start=date(2026, 1, 1), end=date(2026, 1, 31), t1=0.2, t2=0.3, gas=1.1),
        Period(start=date(2026, 1, 31), end=date(2026, 2, 28), t1=0.2, t2=0.3, gas=1.1),
    ]

    with pytest.raises(ValueError, match="must not overlap"):
        _validate_periods(periods)
