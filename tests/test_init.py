"""Tests for integration setup."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import custom_components.energy_prices_manager as integration
from custom_components.energy_prices_manager import http_api


def test_setup_registers_static_panel_and_sidebar_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up the UI with a valid aiohttp static-resource prefix."""
    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    monkeypatch.setattr(integration, "EnergyPricesManagerCoordinator", lambda _: coordinator)

    setup_api = AsyncMock()
    monkeypatch.setattr(http_api, "async_setup_api", setup_api)
    register_panel = MagicMock()
    monkeypatch.setattr(integration, "async_register_built_in_panel", register_panel)

    entry = MagicMock(entry_id="entry-id")

    assert asyncio.run(integration.async_setup_entry(hass, entry))

    static_path = hass.http.async_register_static_paths.call_args.args[0][0]
    assert static_path.url_path == "/energy_prices"
    assert static_path.cache_headers is False
    register_panel.assert_called_once_with(
        hass,
        component_name="iframe",
        sidebar_title="Energy Prices",
        sidebar_icon="mdi:lightning-bolt",
        frontend_url_path="energy-prices",
        require_admin=True,
        config={"url": "/energy_prices/"},
    )
