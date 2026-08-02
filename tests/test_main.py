"""Tests for the App's price-period and helper configuration logic."""

from datetime import date

import pytest

from energy_prices_manager.app import main


def test_validate_periods_sorts_valid_periods() -> None:
    """Valid periods are normalized and sorted by start date."""
    periods = main._validate_periods(
        [
            main.Period(start=date(2026, 7, 1), end=date(2026, 7, 31), t1=0.2, t2=0.3, gas=1.1),
            main.Period(start=date(2026, 1, 1), end=date(2026, 6, 30), t1=0.1, t2=0.2, gas=1.0),
        ]
    )

    assert [period.start for period in periods] == [date(2026, 1, 1), date(2026, 7, 1)]


def test_period_allows_signed_electricity_prices_and_defaults_return_prices() -> None:
    """Electricity can have a negative price and old periods remain compatible."""
    period = main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), t1=-0.2, t2=-0.3, gas=1.1)

    assert period.return_t1 == 0
    assert period.return_t2 == 0


def test_period_allows_signed_returned_electricity_prices() -> None:
    """Returned electricity can either earn or cost money."""
    period = main.Period(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        t1=0.2,
        t2=0.3,
        return_t1=0.1,
        return_t2=-0.1,
        gas=1.1,
    )

    assert period.return_t1 == 0.1
    assert period.return_t2 == -0.1


def test_period_rejects_a_negative_gas_price() -> None:
    """Gas remains a non-negative price."""
    with pytest.raises(ValueError):
        main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), t1=0.2, t2=0.3, gas=-1)


def test_validate_periods_rejects_an_overlap() -> None:
    """Adjacent periods cannot share a date."""
    periods = [
        main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), t1=0.2, t2=0.3, gas=1.1),
        main.Period(start=date(2026, 1, 31), end=date(2026, 2, 28), t1=0.2, t2=0.3, gas=1.1),
    ]

    with pytest.raises(ValueError, match="must not overlap"):
        main._validate_periods(periods)


def test_current_period_selects_only_active_range() -> None:
    """Only the period containing the supplied date is active."""
    periods = [main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), t1=0.2, t2=0.3, gas=1.1)]

    assert main._current_period(periods, date(2026, 1, 15)) == periods[0]
    assert main._current_period(periods, date(2026, 2, 1)) is None


def test_helper_configuration_matches_energy_dashboard_requirements() -> None:
    """The App creates the requested English helpers with precise units/settings."""
    low, high, return_low, return_high, gas = (main._helper_config(helper) for helper in main.HELPERS)

    assert low == {
        "name": "Energy kWh Low (T1) Price",
        "min": -1,
        "max": 1,
        "step": 0.00001,
        "mode": "box",
        "unit_of_measurement": "EUR/kWh",
        "icon": "mdi:currency-eur",
    }
    assert high["name"] == "Energy kWh High (T2) Price"
    assert return_low["name"] == "Energy Return kWh Low (T1) Price"
    assert return_low["min"] == -1
    assert return_low["max"] == 1
    assert return_high["name"] == "Energy Return kWh High (T2) Price"
    assert gas["name"] == "Gas m3 Price"
    assert gas["min"] == 0
    assert gas["max"] == 5
    assert gas["unit_of_measurement"] == "EUR/m³"
