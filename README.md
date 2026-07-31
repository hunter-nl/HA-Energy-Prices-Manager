# Energy Prices Manager for Home Assistant

<img src="brand/logo.svg" alt="Energy Prices Manager" style="max-width: 1000px;">

[![Release][release-badge]][release-url]
[![Validate][validate-badge]][validate-url]
[![CI][ci-badge]][ci-url]
[![License][license-badge]][license-url]
[![Home-Assistant][ha-badge]][ha-url]
[![HACS Custom][hacs-badge]][hacs-url]

[release-badge]: https://img.shields.io/github/v/release/hunter-nl/HA-Energy-Prices-Manager?include_prereleases&sort=semver&display_name=release&label=Release
[release-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/releases
[validate-badge]: https://img.shields.io/github/actions/workflow/status/hunter-nl/HA-Energy-Prices-Manager/validate.yaml?label=Validate
[validate-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/actions/workflows/validate.yaml
[ci-badge]: https://img.shields.io/github/actions/workflow/status/hunter-nl/HA-Energy-Prices-Manager/ci.yaml?label=CI
[ci-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/actions/workflows/ci.yaml
[license-badge]: https://img.shields.io/github/license/hunter-nl/HA-Energy-Prices-Manager?color=blue
[license-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/blob/main/LICENSE
[ha-badge]: https://img.shields.io/badge/Home--Assistant-2026.7.0%2B-green?logo=homeassistant
[ha-url]: https://home-assistant.io
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5?logo=homeassistantcommunitystore&logoColor=white
[hacs-url]: https://www.hacs.xyz/docs/faq/custom_repositories/

Manage electricity (T1/T2) and gas tariff periods directly in Home Assistant with a beautiful web interface, sensor entity, input helpers, and automation blueprint — all distributable via HACS.
It is specially designed for variable/fixed Dutch energy contracts, but can be used for any energy provider with multiple price periods.
No dynamic pricing or external API calls are required, as the integration is fully self-contained.

## What it does

Energy Prices Manager lets you maintain dated electricity and gas price periods
from an admin-only Home Assistant sidebar panel. It selects the active period
for the current date and exposes its T1, T2, and gas prices through
`sensor.energy_prices_current`.

Create three `input_number` helpers for the current prices, then use the
included automation blueprint to keep them synchronized when the active period
changes, Home Assistant starts, or a new day begins.

## Features

- **Web UI** — Beautiful Home Assistant-themed interface for managing price periods
- **Sensor Entity** — `sensor.energy_prices_current` with `t1`, `t2`, `gas` attributes
- **Input Helpers** — Works with `input_number` helpers for T1, T2, and gas prices
- **Automation Blueprint** — Pre-built automation to sync sensor data to helpers
- **Panel + Ingress** — Access via sidebar panel or from anywhere HA is reachable
- **HACS Distribution** — Install and update via HACS with one click

## Requirements

- Home Assistant 2026.7.0 or newer.

## Install

### HACS (Recommended)

1. Open **HACS** → **⋮** → **Custom repositories**
2. Add repository: `hunter-nl/HA-Energy-Prices-Manager`, category: **Integration**
3. Find **Energy Prices Manager** and download it
4. Restart Home Assistant
5. Add **Energy Prices Manager** in **Settings → Devices & services → Add
   integration** and submit it.

### Manual

1. Copy `custom_components/energy_prices_manager` into your Home Assistant
   `/config/custom_components/` directory.
2. Restart Home Assistant
3. Add **Energy Prices Manager** in **Settings → Devices & services → Add
   integration** and submit it.

## Upgrade

### HACS

HACS checks this custom repository for published releases and shows an available
update in **Settings → Updates** (or as **Pending update** in HACS). Before
upgrading, create a Home Assistant backup and read the release notes. Install
the update (by redownload), then restart Home Assistant.

### Manual

1. Create a Home Assistant backup.
2. Replace `/config/custom_components/energy_prices_manager` with the
   `custom_components/energy_prices_manager` directory from the desired release.
3. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"Energy Prices Manager"**
4. Click **"Submit"** (no additional configuration needed)

The integration will automatically:
- Register the web UI panel in the sidebar
- Create the `sensor.energy_prices_current` sensor

### Configure Energy dashboard

1. Create the included **Update Energy Prices from Sensor** automation (see
   [Importing the Blueprint](#importing-the-blueprint)) so the price helpers
   always reflect the active price period.
2. Go to **Settings → Dashboards → Energy** and edit your energy
   configuration.
3. For each electricity consumption source, enable **Use an entity with
   current price** and select the matching helper:
   - `input_number.energy_kwh_low_t1_price` for T1 (low tariff)
   - `input_number.energy_kwh_high_t2_price` for T2 (high tariff)
4. For the gas consumption source, enable **Use an entity with current price**
   and select `input_number.gas_m3_price`.

The Energy dashboard will use the current helper values for new energy data;
historical cost data is not recalculated when prices change.

## Using the Web Interface

Access the web interface via:
- **Sidebar**: Click the "Energy Prices" icon in the Home Assistant sidebar
- **Direct URL**: `http://<your-ha-url>/energy_prices/`

The interface allows you to:
- View the current active price period
- Add/edit/delete price periods
- Set start/end dates and prices for T1 (low), T2 (high), and gas
- Validate periods for overlaps and invalid values
- Save changes with instant sensor updates

## Sensor Entity

The integration exposes `sensor.energy_prices_current` with the following attributes:

| Attribute | Description |
|-----------|-------------|
| `state` | Current period label (e.g., "2026-06-16 to 2026-09-15") |
| `t1` | Low electricity price (€/kWh) |
| `t2` | High electricity price (€/kWh) |
| `gas` | Gas price (€/m³) |
| `start` | Start date of current period |
| `end` | End date of current period |

### Example Usage in Templates

```yaml
# Get current T1 price
{{ state_attr('sensor.energy_prices_current', 't1') }}

# Get current T2 price
{{ state_attr('sensor.energy_prices_current', 't2') }}

# Get current gas price
{{ state_attr('sensor.energy_prices_current', 'gas') }}
```

## Input Helpers

Create these input_number helpers before importing the automation blueprint:

| Entity ID | Description |
|-----------|-------------|
| `input_number.energy_kwh_low_t1_price` | Low electricity (T1) price |
| `input_number.energy_kwh_high_t2_price` | High electricity (T2) price |
| `input_number.gas_m3_price` | Gas price |

## Automation Blueprint

The integration includes a pre-built automation blueprint that:
- Triggers daily at 00:00:01
- Triggers on Home Assistant start
- Triggers when the sensor state changes
- Updates all 3 input_number helpers with the current prices

### Importing the Blueprint

Before importing the Blueprint, create first the [Input Helpers](#input-helpers)

1. Go to **Settings → Automations & Scripts**
2. Click **"Create new automation"**
3. Click **"Choose a blueprint"**
4. Select **"Update Energy Prices from Sensor"**
5. Configure the sensor and helper entities (the defaults match the documented
   helper IDs)
6. Save the automation

### Manual YAML Installation

If you prefer manual YAML installation, add this to your `automations.yaml`:

```yaml
alias: Update Energy Prices
description: Update electricity and gas prices using the addon sensor
triggers:
    - trigger: time
      at: "00:00:01"
    - trigger: homeassistant
      event: start
    - trigger: state
      entity_id: sensor.energy_prices_current
actions:
    - choose:
        - conditions:
            - condition: template
              value_template: |
                {{ trigger.platform != 'state' }}
        sequence:
            - action: homeassistant.update_entity
              target:
                 entity_id: sensor.energy_prices_current
    - wait_template: |
        {{
        state_attr('sensor.energy_prices_current', 't1') is not none and
        state_attr('sensor.energy_prices_current', 't2') is not none and
        state_attr('sensor.energy_prices_current', 'gas') is not none
        }}
     timeout: "00:00:30"
    - action: input_number.set_value
     target:
       entity_id: input_number.energy_kwh_high_t2_price
     data:
       value: "{{ state_attr('sensor.energy_prices_current', 't2') | float }}"
    - action: input_number.set_value
     target:
       entity_id: input_number.energy_kwh_low_t1_price
     data:
       value: "{{ state_attr('sensor.energy_prices_current', 't1') | float }}"
    - action: input_number.set_value
     target:
       entity_id: input_number.gas_m3_price
     data:
       value: "{{ state_attr('sensor.energy_prices_current', 'gas') | float }}"
mode: restart
```

## API Endpoints

The integration exposes the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/energy_prices/current` | GET | Get current active period |
| `/api/energy_prices/periods` | GET | Get all periods |
| `/api/energy_prices/periods` | POST | Save all periods (admin only) |
| `/api/energy_prices/ping` | GET | Health check |

### Example: Get Current Period

```bash
curl -H "Authorization: Bearer <your-long-lived-access-token>" \
     http://localhost:8123/api/energy_prices/current
```

### Example: Save Periods

```bash
curl -X POST \
     -H "Authorization: Bearer <your-long-lived-access-token>" \
     -H "Content-Type: application/json" \
     -d '[{"start":"2026-01-01","end":"2026-03-15","t1":0.25,"t2":0.30,"gas":1.20}]' \
     http://localhost:8123/api/energy_prices/periods
```

## Troubleshooting

### Integration not appearing in HACS

1. Make sure you've added the repository as a custom repository in HACS
2. Click the three dots → "Check for updates" in HACS
3. Restart Home Assistant

### Sensor showing "unavailable"

1. Make sure you've added at least one price period via the web UI
2. Check that the period dates include today's date
3. Check Home Assistant logs for any errors

### Helpers missing from the automation

1. Go to **Settings → Devices & Services → Helpers**
2. Create these input_number helpers:
   - `energy_kwh_low_t1_price` (Low T1 price)
   - `energy_kwh_high_t2_price` (High T2 price)
   - `gas_m3_price` (Gas price)


## Support

- [GitHub Issues](https://github.com/hunter-nl/HA-Energy-Prices-Manager/issues)
- [Home Assistant Community](https://community.home-assistant.io/)


## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
