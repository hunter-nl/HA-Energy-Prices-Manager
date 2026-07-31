"""Tests for frontend API routing."""

from pathlib import Path


def test_frontend_uses_energy_prices_api_base() -> None:
    """The panel must call the API views registered by the integration."""
    app = (Path(__file__).parents[1] / "custom_components" / "energy_prices_manager" / "www" / "app.js").read_text()

    assert "const API_BASE = `${BASE_PATH}/api/energy_prices`;" in app
    assert "fetch(`${API_BASE}/periods`)" in app
    assert "fetch(`${API_BASE}/current`)" in app
