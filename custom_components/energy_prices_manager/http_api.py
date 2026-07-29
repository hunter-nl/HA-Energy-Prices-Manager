"""HTTP API for Energy Prices Manager."""

from __future__ import annotations

from datetime import date
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView, require_admin
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import DOMAIN, _get_store

API_BASE = "/api/energy_prices"
PRICE_KEYS = ("t1", "t2", "gas")


def _validate_periods(body: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate and normalize the persisted price periods."""
    if not isinstance(body, list):
        return [], ["Expected a list of price periods."]

    errors: list[str] = []
    periods: list[dict[str, Any]] = []
    for index, item in enumerate(body, start=1):
        if not isinstance(item, dict):
            errors.append(f"Row {index}: expected an object.")
            continue

        start = item.get("start")
        end = item.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            errors.append(f"Row {index}: start and end must be ISO dates.")
            continue

        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except ValueError:
            errors.append(f"Row {index}: start and end must be ISO dates.")
            continue

        if start_date > end_date:
            errors.append(f"Row {index}: start date must be before or equal to end date.")
            continue

        prices: dict[str, float] = {}
        for key in PRICE_KEYS:
            value = item.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                errors.append(f"Row {index}: {key} must be a non-negative number.")
                continue
            prices[key] = float(value)

        if len(prices) == len(PRICE_KEYS):
            periods.append({"start": start, "end": end, **prices})

    periods.sort(key=lambda period: period["start"])
    for previous, current in zip(periods, periods[1:], strict=False):
        if previous["end"] >= current["start"]:
            errors.append(
                f"Periods {previous['start']} to {previous['end']} and {current['start']} to {current['end']} overlap."
            )

    return periods, errors


class EnergyPricesCurrentView(HomeAssistantView):
    """Return the currently active price period."""

    url = f"{API_BASE}/current"
    name = "api:energy_prices:current"

    async def get(self, request: web.Request) -> web.Response:
        """Get the current active price period."""
        hass: HomeAssistant = request.app["hass"]
        periods = await _get_store(hass).async_load() or []
        today = dt_util.now().date().isoformat()
        for period in periods:
            if period.get("start", "") <= today <= period.get("end", ""):
                return self.json(period)
        return self.json({"detail": "No active period"})


class EnergyPricesPeriodsView(HomeAssistantView):
    """Get and save all price periods."""

    url = f"{API_BASE}/periods"
    name = "api:energy_prices:periods"

    async def get(self, request: web.Request) -> web.Response:
        """Get all saved price periods."""
        hass: HomeAssistant = request.app["hass"]
        return self.json(await _get_store(hass).async_load() or [])

    @require_admin
    async def post(self, request: web.Request) -> web.Response:
        """Validate and save all price periods."""
        try:
            body = await request.json()
        except ValueError, web.HTTPBadRequest:
            return self.json({"detail": ["Request body must be valid JSON."]}, status_code=400)

        periods, errors = _validate_periods(body)
        if errors:
            return self.json({"detail": errors}, status_code=400)

        hass: HomeAssistant = request.app["hass"]
        await _get_store(hass).async_save(periods)
        for coordinator in hass.data.get(DOMAIN, {}).values():
            if hasattr(coordinator, "async_request_refresh"):
                await coordinator.async_request_refresh()

        return self.json({"status": "ok", "saved": len(periods)})


class EnergyPricesPingView(HomeAssistantView):
    """Health check."""

    url = f"{API_BASE}/ping"
    name = "api:energy_prices:ping"

    async def get(self, request: web.Request) -> web.Response:
        """Return the API health status."""
        return self.json({"status": "ok"})


async def async_setup_api(hass: HomeAssistant) -> None:
    """Register all API views with the Home Assistant HTTP server."""
    hass.http.register_view(EnergyPricesCurrentView)
    hass.http.register_view(EnergyPricesPeriodsView)
    hass.http.register_view(EnergyPricesPingView)
