"""Sensor platform for Energy Prices Manager."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, EnergyPricesManagerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: EnergyPricesManagerCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([EnergyPricesCurrentSensor(coordinator)])


class EnergyPricesCurrentSensor(CoordinatorEntity[EnergyPricesManagerCoordinator], SensorEntity):
    """Sensor representing the current active energy price period."""

    _attr_has_entity_name = True
    _attr_name = "Current Prices"
    _attr_unique_id = "energy_prices_current"
    _attr_icon = "mdi:lightning-bolt"

    def __init__(self, coordinator: EnergyPricesManagerCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    async def async_update(self) -> None:
        """Refresh periods when Home Assistant explicitly updates the sensor."""
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return bool(self.coordinator.periods)

    @property
    def native_value(self) -> str | None:
        """Return the current active period label."""
        active = self.coordinator.current_period
        if active is None:
            return None
        return f"{active['start']} to {active['end']}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the price attributes."""
        active = self.coordinator.current_period
        if active is None:
            return {"t1": None, "t2": None, "gas": None, "start": None, "end": None}
        return {
            "t1": active.get("t1"),
            "t2": active.get("t2"),
            "gas": active.get("gas"),
            "start": active.get("start"),
            "end": active.get("end"),
        }
