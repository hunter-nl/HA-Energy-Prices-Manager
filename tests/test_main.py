"""Tests for the App's price-period and helper configuration logic."""

import json
import os
from datetime import date
from pathlib import Path

import pytest

from energy_prices_manager.app import main


def test_validate_periods_sorts_valid_periods() -> None:
    """Valid periods are normalized and sorted by start date."""
    periods = main._validate_periods(
        [
            main.Period(
                start=date(2026, 7, 1),
                end=date(2026, 7, 31),
                import_t1=0.2,
                import_t2=0.3,
                gas=1.1,
            ),
            main.Period(
                start=date(2026, 1, 1),
                end=date(2026, 6, 30),
                import_t1=0.1,
                import_t2=0.2,
                gas=1.0,
            ),
        ]
    )

    assert [period.start for period in periods] == [date(2026, 1, 1), date(2026, 7, 1)]


def test_load_periods_migrates_legacy_electricity_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Existing stored periods migrate before the renamed API is used."""
    data_file = tmp_path / "energy_prices.json"
    data_file.write_text(
        json.dumps(
            [
                {
                    "start": "2026-01-01",
                    "end": "2026-01-31",
                    "t1": -0.2,
                    "t2": -0.3,
                    "return_t1": 0.1,
                    "return_t2": -0.1,
                    "gas": 1.1,
                }
            ]
        )
    )
    monkeypatch.setattr(main, "DATA_FILE", data_file)

    periods = main._load_periods()

    assert periods[0].model_dump(mode="json") == {
        "start": "2026-01-01",
        "end": "2026-01-31",
        "import_t1": -0.2,
        "import_t2": -0.3,
        "export_t1": 0.1,
        "export_t2": -0.1,
        "gas": 1.1,
    }
    assert json.loads(data_file.read_text()) == [periods[0].model_dump(mode="json")]


def test_period_rejects_legacy_api_fields() -> None:
    """The public API exposes only the renamed import/export fields."""
    with pytest.raises(ValueError):
        main.Period.model_validate(
            {
                "start": "2026-01-01",
                "end": "2026-01-31",
                "t1": 0.2,
                "t2": 0.3,
                "gas": 1.1,
            }
        )


def test_period_allows_signed_export_electricity_prices() -> None:
    """Exported electricity can either earn or cost money."""
    period = main.Period(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
        import_t1=0.2,
        import_t2=0.3,
        export_t1=0.1,
        export_t2=-0.1,
        gas=1.1,
    )

    assert period.export_t1 == 0.1
    assert period.export_t2 == -0.1


def test_period_rejects_a_negative_gas_price() -> None:
    """Gas remains a non-negative price."""
    with pytest.raises(ValueError):
        main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), import_t1=0.2, import_t2=0.3, gas=-1)


def test_validate_periods_rejects_an_overlap() -> None:
    """Adjacent periods cannot share a date."""
    periods = [
        main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), import_t1=0.2, import_t2=0.3, gas=1.1),
        main.Period(start=date(2026, 1, 31), end=date(2026, 2, 28), import_t1=0.2, import_t2=0.3, gas=1.1),
    ]

    with pytest.raises(ValueError, match="must not overlap"):
        main._validate_periods(periods)


def test_current_period_selects_only_active_range() -> None:
    """Only the period containing the supplied date is active."""
    periods = [main.Period(start=date(2026, 1, 1), end=date(2026, 1, 31), import_t1=0.2, import_t2=0.3, gas=1.1)]

    assert main._current_period(periods, date(2026, 1, 15)) == periods[0]
    assert main._current_period(periods, date(2026, 2, 1)) is None


def test_helper_configuration_matches_energy_dashboard_requirements() -> None:
    """The App creates the requested English helpers with precise units/settings."""
    import_t1, import_t2, export_t1, export_t2, gas = (main._helper_config(helper) for helper in main.HELPERS)

    assert [helper["entity_id"] for helper in main.HELPERS] == [
        "input_number.electricity_import_t1_price",
        "input_number.electricity_import_t2_price",
        "input_number.electricity_export_t1_price",
        "input_number.electricity_export_t2_price",
        "input_number.gas_m3_price",
    ]

    assert import_t1 == {
        "name": "Electricity Import (T1) Price",
        "min": -1,
        "max": 1,
        "step": 0.00001,
        "mode": "box",
        "unit_of_measurement": "EUR/kWh",
        "icon": "mdi:currency-eur",
    }
    assert import_t2["name"] == "Electricity Import (T2) Price"
    assert export_t1["name"] == "Electricity Export (T1) Price"
    assert export_t1["min"] == -1
    assert export_t1["max"] == 1
    assert export_t2["name"] == "Electricity Export (T2) Price"
    assert gas["name"] == "Gas m3 Price"
    assert gas["min"] == 0
    assert gas["max"] == 5
    assert gas["unit_of_measurement"] == "EUR/m³"


def test_ingress_assets_are_not_cached() -> None:
    """An App upgrade must not leave a cached UI using a changed API schema."""
    static_files = main.NoCacheStaticFiles(directory=main.WEB_DIR, html=True)
    index_file = main.WEB_DIR / "index.html"

    response = static_files.file_response(
        index_file,
        os.stat(index_file),
        {"type": "http", "method": "GET", "path": "/", "headers": []},
    )

    assert response.headers["cache-control"] == "no-store, max-age=0"
