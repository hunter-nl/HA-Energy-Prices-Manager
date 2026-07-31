"""Ingress application for managing energy-price periods."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from websockets.asyncio.client import connect

DATA_FILE = Path("/data/energy_prices.json")
CORE_API_URL = "http://supervisor/core/api"
CORE_WS_URL = "ws://supervisor/core/websocket"
WEB_DIR = Path(
    os.environ.get(
        "ENERGY_PRICES_WEB_DIR",
        Path(__file__).parents[1] / "custom_components" / "energy_prices_manager" / "www",
    )
)
LOGGER = logging.getLogger(__name__)


class Period(BaseModel):
    """A dated set of energy prices."""

    start: date
    end: date
    t1: float = Field(ge=0)
    t2: float = Field(ge=0)
    gas: float = Field(ge=0)


HELPERS = (
    {
        "entity_id": "input_number.energy_kwh_low_t1_price",
        "name": "Energy kWh Low (T1) Price",
        "unit_of_measurement": "EUR/kWh",
        "maximum": 1,
        "price_key": "t1",
    },
    {
        "entity_id": "input_number.energy_kwh_high_t2_price",
        "name": "Energy kWh High (T2) Price",
        "unit_of_measurement": "EUR/kWh",
        "maximum": 1,
        "price_key": "t2",
    },
    {
        "entity_id": "input_number.gas_m3_price",
        "name": "Gas m3 Price",
        "unit_of_measurement": "EUR/m³",
        "maximum": 5,
        "price_key": "gas",
    },
)


def _load_periods() -> list[Period]:
    if not DATA_FILE.exists():
        return []
    return [Period.model_validate(item) for item in json.loads(DATA_FILE.read_text())]


def _validate_periods(periods: list[Period]) -> list[Period]:
    periods = sorted(periods, key=lambda period: period.start)
    for period in periods:
        if period.start > period.end:
            raise ValueError("A period's start date must not be after its end date.")
    for previous, current in zip(periods, periods[1:], strict=False):
        if previous.end >= current.start:
            raise ValueError("Periods must not overlap.")
    return periods


def _save_periods(periods: list[Period]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps([period.model_dump(mode="json") for period in periods], indent=2))


def _current_period(periods: list[Period], today: date | None = None) -> Period | None:
    today = today or date.today()
    return next((period for period in periods if period.start <= today <= period.end), None)


async def _ws_command(command: dict[str, Any]) -> Any:
    """Run an authenticated Home Assistant WebSocket command."""
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise RuntimeError("SUPERVISOR_TOKEN is unavailable; enable homeassistant_api.")
    async with connect(CORE_WS_URL) as websocket:
        await websocket.recv()
        await websocket.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(await websocket.recv()).get("type") != "auth_ok":
            raise RuntimeError("Home Assistant WebSocket authentication failed.")
        command["id"] = 1
        await websocket.send(json.dumps(command))
        response = json.loads(await websocket.recv())
        if not response.get("success"):
            raise RuntimeError(response.get("error", {}).get("message", "WebSocket command failed."))
        return response["result"]


async def _ensure_helpers() -> None:
    """Create or normalize the app-managed English price helpers."""
    existing = {item["name"]: item for item in await _ws_command({"type": "input_number/list"})}
    for helper in HELPERS:
        config = {
            "name": helper["name"],
            "min": 0,
            "max": helper["maximum"],
            "step": 0.00001,
            "mode": "box",
            "unit_of_measurement": helper["unit_of_measurement"],
            "icon": "mdi:currency-eur",
        }
        if item := existing.get(helper["name"]):
            await _ws_command({"type": "input_number/update", "input_number_id": item["id"], **config})
        else:
            await _ws_command({"type": "input_number/create", **config})


async def _sync_helpers() -> None:
    """Write the active period's values into Home Assistant helpers."""
    period = _current_period(_load_periods())
    if period is None:
        return
    token = os.environ["SUPERVISOR_TOKEN"]
    import urllib.request

    for helper in HELPERS:
        payload = json.dumps(
            {"entity_id": helper["entity_id"], "value": getattr(period, str(helper["price_key"]))}
        ).encode()
        request = urllib.request.Request(
            f"{CORE_API_URL}/services/input_number/set_value",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        await asyncio.to_thread(urllib.request.urlopen, request)


async def _daily_sync() -> None:
    while True:
        tomorrow = datetime.combine(date.today() + timedelta(days=1), time.min)
        await asyncio.sleep((tomorrow - datetime.now()).total_seconds() + 1)
        await _sync_helpers()


@asynccontextmanager
async def _lifespan(_: FastAPI):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        await _ensure_helpers()
        await _sync_helpers()
    except (OSError, RuntimeError) as err:
        LOGGER.exception("Unable to initialize Home Assistant helpers: %s", err)
    task = asyncio.create_task(_daily_sync())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Energy Prices Manager", lifespan=_lifespan)
app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Open the Ingress user interface."""
    return RedirectResponse("web/")


@app.get("/api/current")
async def get_current() -> dict[str, Any]:
    period = _current_period(_load_periods())
    return period.model_dump(mode="json") if period else {"detail": "No active period"}


@app.get("/api/periods")
async def get_periods() -> list[dict[str, Any]]:
    return [period.model_dump(mode="json") for period in _load_periods()]


@app.post("/api/periods")
async def save_periods(periods: list[Period]) -> dict[str, int | str]:
    try:
        periods = _validate_periods(periods)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=[str(err)]) from err
    _save_periods(periods)
    await _sync_helpers()
    return {"status": "ok", "saved": len(periods)}
