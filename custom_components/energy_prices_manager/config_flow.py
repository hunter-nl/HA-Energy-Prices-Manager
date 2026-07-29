"""Config flow for Energy Prices Manager."""

from __future__ import annotations

from typing import Any

import homeassistant.config_entries as config_entries
import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult

from . import DOMAIN

CONFIG_SCHEMA = vol.Schema({vol.Optional("name", default="Energy Prices Manager"): str})


class EnergyPricesManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Prices Manager."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial config step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get("name", "Energy Prices Manager"),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )
