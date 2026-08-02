"""Ingress application for managing energy-price periods."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal, TypedDict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from websockets.asyncio.client import connect

DATA_FILE = Path("/data/energy_prices.json")
CORE_API_URL = "http://supervisor/core/api"
CORE_WS_URL = "ws://supervisor/core/websocket"
WEB_DIR = Path(__file__).parents[1] / "web"
LOGGER = logging.getLogger(__name__)


class Helper(TypedDict):
    """Definition of an App-managed Home Assistant helper."""

    entity_id: str
    name: str
    unit_of_measurement: str
    minimum: int
    maximum: int
    price_key: Literal["t1", "t2", "return_t1", "return_t2", "gas"]


class Period(BaseModel):
    """A dated set of energy prices."""

    start: date
    end: date
    t1: float
    t2: float
    return_t1: float = 0
    return_t2: float = 0
    gas: float = Field(ge=0)


HELPERS: tuple[Helper, ...] = (
    {
        "entity_id": "input_number.energy_kwh_low_t1_price",
        "name": "Energy kWh Low (T1) Price",
        "unit_of_measurement": "EUR/kWh",
        "minimum": -1,
        "maximum": 1,
        "price_key": "t1",
    },
    {
        "entity_id": "input_number.energy_kwh_high_t2_price",
        "name": "Energy kWh High (T2) Price",
        "unit_of_measurement": "EUR/kWh",
        "minimum": -1,
        "maximum": 1,
        "price_key": "t2",
    },
    {
        "entity_id": "input_number.energy_return_kwh_low_t1_price",
        "name": "Energy Return kWh Low (T1) Price",
        "unit_of_measurement": "EUR/kWh",
        "minimum": -1,
        "maximum": 1,
        "price_key": "return_t1",
    },
    {
        "entity_id": "input_number.energy_return_kwh_high_t2_price",
        "name": "Energy Return kWh High (T2) Price",
        "unit_of_measurement": "EUR/kWh",
        "minimum": -1,
        "maximum": 1,
        "price_key": "return_t2",
    },
    {
        "entity_id": "input_number.gas_m3_price",
        "name": "Gas m3 Price",
        "unit_of_measurement": "EUR/m³",
        "minimum": 0,
        "maximum": 5,
        "price_key": "gas",
    },
)


def _load_periods() -> list[Period]:
    if not DATA_FILE.exists():
        return []
    return [Period.model_validate(item) for item in json.loads(DATA_FILE.read_text())]


def _validate_periods(periods: list[Period]) -> list[Period]:
    ordered_periods = sorted(periods, key=lambda period: period.start)
    for period in ordered_periods:
        if period.start > period.end:
            raise ValueError("A period's start date must not be after its end date.")
    for previous, current in zip(ordered_periods, ordered_periods[1:], strict=False):
        if previous.end >= current.start:
            raise ValueError("Periods must not overlap.")
    return ordered_periods


def _save_periods(periods: list[Period]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps([period.model_dump(mode="json") for period in periods], indent=2))


def _current_period(periods: list[Period], today: date | None = None) -> Period | None:
    active_date = today or date.today()
    return next((period for period in periods if period.start <= active_date <= period.end), None)


def _helper_config(helper: Helper) -> dict[str, Any]:
    return {
        "name": helper["name"],
        "min": helper["minimum"],
        "max": helper["maximum"],
        "step": 0.00001,
        "mode": "box",
        "unit_of_measurement": helper["unit_of_measurement"],
        "icon": "mdi:currency-eur",
    }


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
        await websocket.send(json.dumps({"id": 1, **command}))
        response = json.loads(await websocket.recv())
        if not response.get("success"):
            raise RuntimeError(response.get("error", {}).get("message", "WebSocket command failed."))
        return response["result"]


async def _ensure_helpers() -> None:
    """Create or normalize the app-managed English price helpers."""
    existing = {item["name"]: item for item in await _ws_command({"type": "input_number/list"})}
    for helper in HELPERS:
        config = _helper_config(helper)
        if item := existing.get(helper["name"]):
            await _ws_command({"type": "input_number/update", "input_number_id": item["id"], **config})
        else:
            await _ws_command({"type": "input_number/create", **config})


def _set_helper_value(entity_id: str, value: float) -> None:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise RuntimeError("SUPERVISOR_TOKEN is unavailable; enable homeassistant_api.")
    request = urllib.request.Request(
        f"{CORE_API_URL}/services/input_number/set_value",
        data=json.dumps({"entity_id": entity_id, "value": value}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        pass


async def _sync_helpers() -> None:
    """Write the active period's values into Home Assistant helpers."""
    period = _current_period(_load_periods())
    if period is None:
        return
    for helper in HELPERS:
        await asyncio.to_thread(_set_helper_value, helper["entity_id"], getattr(period, helper["price_key"]))


async def _daily_sync() -> None:
    while True:
        tomorrow = datetime.combine(date.today() + timedelta(days=1), time.min)
        await asyncio.sleep((tomorrow - datetime.now()).total_seconds() + 1)
        try:
            await _sync_helpers()
        except (OSError, RuntimeError, urllib.error.URLError) as err:
            LOGGER.exception("Unable to update price helpers: %s", err)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        await _ensure_helpers()
        await _sync_helpers()
    except (OSError, RuntimeError, urllib.error.URLError) as err:
        LOGGER.exception("Unable to initialize Home Assistant helpers: %s", err)
    task = asyncio.create_task(_daily_sync())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Energy Prices Manager", lifespan=_lifespan)


@app.get("/api/current")
async def get_current() -> dict[str, Any]:
    """Return the current price period, if one is active today."""
    period = _current_period(_load_periods())
    return period.model_dump(mode="json") if period else {"detail": "No active period"}


@app.get("/api/periods")
async def get_periods() -> list[dict[str, Any]]:
    """Return saved price periods."""
    return [period.model_dump(mode="json") for period in _load_periods()]


@app.post("/api/periods")
async def save_periods(periods: list[Period]) -> dict[str, int | str]:
    """Validate, persist, and immediately synchronize price helpers."""
    try:
        periods = _validate_periods(periods)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=[str(err)]) from err
    _save_periods(periods)
    try:
        await _sync_helpers()
    except (OSError, RuntimeError, urllib.error.URLError) as err:
        LOGGER.exception("Saved periods but could not update helpers: %s", err)
        raise HTTPException(status_code=503, detail=["Periods were saved, but helpers could not be updated."]) from err
    return {"status": "ok", "saved": len(periods)}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
