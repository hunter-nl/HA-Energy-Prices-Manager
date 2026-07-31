# Energy Prices Manager

Energy Prices Manager is a Home Assistant App (formerly add-on) for maintaining dated electricity and gas tariff periods. Its web interface is delivered through Home Assistant Ingress, so it is available in the sidebar without a separate login.

## Requirements

- Home Assistant 2026.7.0 or newer with Supervisor support.

## Install

1. In Home Assistant, open **Settings → Apps → App store**.
2. Open the app-store menu, choose **Repositories**, and add
   `https://github.com/hunter-nl/HA-Energy-Prices-Manager`.
3. Install **Energy Prices Manager** and open it from the sidebar.

HACS does not install Supervisor Apps. It installs integrations to
`/config/custom_components`, which is not an App repository location.

### Manual local installation

Use this method for local development or to test an unreleased change. It
requires Home Assistant OS or a Supervised installation, plus the SSH or Samba
App to access the host's App directory.

1. Copy or clone this repository to
   `/addons/local/energy_prices_manager` (note the plural `/addons`):

   ```bash
   git clone https://github.com/hunter-nl/HA-Energy-Prices-Manager.git \
     /addons/local/energy_prices_manager
   ```

2. In **Settings → Apps → App store**, open the menu and select **Reload**.
3. Find **Energy Prices Manager** in the **Local Apps** repository, install it,
   and start it.

For a local update, replace the files in that directory, reload the App store,
and use **Rebuild** from the App page before starting the updated App.

## About the App repository

`repository.yaml` identifies this Git repository to the Home Assistant App
store. `config.yaml` identifies the Energy Prices Manager App itself, including
its Ingress endpoint, architecture support, and required access to the Home
Assistant Core API. Supervisor builds the App image, persists `/data`, proxies
the sidebar UI through Ingress, and supplies the `SUPERVISOR_TOKEN` used to
create and update the helpers.

The app creates and maintains these English `input_number` helpers:

| Entity ID | Name | Unit |
| --- | --- | --- |
| `input_number.energy_kwh_low_t1_price` | Energy kWh Low (T1) Price | EUR/kWh |
| `input_number.energy_kwh_high_t2_price` | Energy kWh High (T2) Price | EUR/kWh |
| `input_number.gas_m3_price` | Gas m3 Price | EUR/m³ |

When periods are saved, and shortly after each midnight, the app writes the active period's values to those helpers. If no period is active, it leaves the current helper values unchanged.

## Data

Periods are stored in the app's persistent `/data/energy_prices.json` volume. Updating or restarting the app does not remove the configured periods.

## Development

Run the local checks with:

```bash
uv sync --extra dev
uv run python -m pytest
uv run ruff check
uv run ruff format --check
uv run ty check
```
