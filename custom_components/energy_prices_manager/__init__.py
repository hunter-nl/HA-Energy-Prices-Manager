"""Energy Prices Manager integration for Home Assistant."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import storage
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

DOMAIN = "energy_prices_manager"
STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN
PLATFORMS = ["sensor"]

logger = logging.getLogger(__name__)


def _get_store(hass: HomeAssistant) -> storage.Store:
    """Return the storage.Store instance."""
    return storage.Store(hass, STORAGE_VERSION, STORAGE_KEY)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Energy Prices Manager from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})

    coordinator = EnergyPricesManagerCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    domain_data[entry.entry_id] = coordinator

    if not domain_data.get("_resources_registered"):
        from .http_api import async_setup_api

        await async_setup_api(hass)

        www_path = Path(__file__).parent / "www"
        await hass.http.async_register_static_paths(
            [StaticPathConfig("/energy_prices", str(www_path), cache_headers=False)]
        )

        async_register_built_in_panel(
            hass,
            component_name="iframe",
            sidebar_title="Energy Prices",
            sidebar_icon="mdi:lightning-bolt",
            frontend_url_path="energy-prices",
            require_admin=True,
            config={"url": "/energy_prices/index.html"},
        )
        domain_data["_resources_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Energy Prices Manager."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class EnergyPricesManagerCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinate price-period data stored by the integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name="Energy Prices Manager",
            update_interval=timedelta(hours=1),
        )
        self._store = _get_store(hass)

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Load price periods from storage."""
        return await self._store.async_load() or []

    @property
    def periods(self) -> list[dict[str, Any]]:
        """Return all configured price periods."""
        return self.data or []

    @property
    def current_period(self) -> dict[str, Any] | None:
        """Return the period active in Home Assistant's configured timezone."""
        today = dt_util.now().date().isoformat()
        for period in self.periods:
            if period.get("start", "") <= today <= period.get("end", ""):
                return period
        return None
