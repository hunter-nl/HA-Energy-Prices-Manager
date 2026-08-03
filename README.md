# Energy Prices Manager

<img src="https://raw.githubusercontent.com/hunter-nl/HA-Energy-Prices-Manager/main/brand/logo.png" alt="Energy Prices Manager" width="480">

[![Release][release-badge]][release-url]
[![CI][ci-badge]][ci-url]
[![License][license-badge]][license-url]
[![Home Assistant][ha-badge]][ha-url]

[release-badge]: https://img.shields.io/github/v/release/hunter-nl/HA-Energy-Prices-Manager?include_prereleases&sort=semver&display_name=release&label=Release
[release-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/releases
[ci-badge]: https://img.shields.io/github/actions/workflow/status/hunter-nl/HA-Energy-Prices-Manager/ci.yaml?label=CI
[ci-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/actions/workflows/ci.yaml
[license-badge]: https://img.shields.io/github/license/hunter-nl/HA-Energy-Prices-Manager?color=blue
[license-url]: https://github.com/hunter-nl/HA-Energy-Prices-Manager/blob/main/LICENSE
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2026.7.0%2B-41BDF5?logo=home-assistant
[ha-url]: https://www.home-assistant.io/

Energy Prices Manager is a Home Assistant App for maintaining fixed or variable
electricity and gas tariff periods. Its Ingress page appears in the sidebar and
needs no separate browser authentication.

The App creates and manages these helpers for the Energy dashboard:

| Helper | Entity ID | Unit | Range |
| --- | --- | --- | --- |
| Electricity Import (T1) Price | `input_number.electricity_import_t1_price` | EUR/kWh | -1–1 |
| Electricity Import (T2) Price | `input_number.electricity_import_t2_price` | EUR/kWh | -1–1 |
| Electricity Export (T1) Price | `input_number.electricity_export_t1_price` | EUR/kWh | -1–1 |
| Electricity Export (T2) Price | `input_number.electricity_export_t2_price` | EUR/kWh | -1–1 |
| Gas m3 Price | `input_number.gas_m3_price` | EUR/m³ | 0–5 |

All helpers use an input field, a `0.00001` step, and `mdi:currency-eur`.
They are created/normalised when the App starts, updated immediately when a
period is saved, and refreshed shortly after midnight. No separate sensor or
automation is needed.

### Breaking helper rename

The Import/Export helper names and entity IDs replace the previous Low/High
and Return helper IDs. Update your Energy dashboard price selections to the
new helpers after upgrading. Existing helpers are left untouched so you can
migrate dashboard references safely; they are no longer updated by the App.
The period API now uses `import_t1`, `import_t2`, `export_t1`, and `export_t2`.
Existing saved periods with the previous field names remain readable, but API
responses and future saves use the new field names.

## Install from this App repository

This is a Home Assistant App repository. Install it from the Home Assistant App
Store using the repository URL below.

1. In Home Assistant, open **Settings → Apps → App Store**.
2. Open the menu, choose **Repositories**, then add
   `https://github.com/hunter-nl/HA-Energy-Prices-Manager`.
3. Find **Energy Prices Manager**, install it, and start it.
4. Open **Energy Prices** from the sidebar and add your price periods.

Released versions are distributed as Docker images through GitHub Container
Registry. Home Assistant automatically downloads the image matching its CPU
architecture; end users do not need Docker, a zip file, or a manual image
build.

## Manual local installation (development only)

This route is useful for quick testing on your own Home Assistant instance. It
is not the recommended end-user installation route, especially on HAOS.

1. Copy the repository's `energy_prices_manager` folder to
   `/addons/local/energy_prices_manager` on the Home Assistant host.
2. In the copied `config.yaml`, temporarily comment out the `image:` line so
   Supervisor builds the local `Dockerfile`.
3. Open **Settings → Apps → App Store**, refresh the page, then install and
   start **Energy Prices Manager**.

The App keeps its periods in its persistent `/data` directory, so updates do
not discard them.

## Configure the Energy dashboard

In the Energy dashboard configuration, select the managed helper that matches
your tariff:

- `input_number.electricity_import_t1_price` for T1 electricity imported from the grid.
- `input_number.electricity_import_t2_price` for T2 electricity imported from the grid.
- `input_number.electricity_export_t1_price` for T1 electricity exported to the grid.
- `input_number.electricity_export_t2_price` for T2 electricity exported to the grid.
- `input_number.gas_m3_price` for gas.

Configure the two electricity-export helpers as the grid source's **Return to
grid** prices. A positive export price is compensation paid to you; a negative
price is a charge for exporting electricity. Import electricity prices can also
be negative for dynamic contracts, indicating that you are paid to consume
electricity from the grid.

Home Assistant uses current price helpers for new energy data; changing a
period does not retroactively recalculate historical costs.

## Development and releases

The App lives entirely in [`energy_prices_manager`](energy_prices_manager).
`repository.yaml` makes the GitHub repository discoverable by Home Assistant.

The release process is deliberately image-based:

1. **Prepare release** updates the App config, Python metadata, and changelog
   in a reviewable release PR.
2. Merging that PR triggers **Publish release**.
3. The workflow builds and pushes a versioned image for every Home Assistant
   App architecture (`amd64` and `aarch64`) to GHCR, then creates the GitHub
   release.

The App configuration references the generic multi-architecture image
`ghcr.io/hunter-nl/energy-prices-manager:<version>`. The publishing workflow
builds the per-architecture images behind it, then publishes one manifest that
lets Home Assistant select the correct architecture automatically. The version
in `energy_prices_manager/config.yaml` and every published image tag are always
the same.

The Dockerfile is the source of truth for local and CI builds. It carries the
required Home Assistant image labels plus OCI title, description, source, and
license metadata.

Before the first public release, the repository owner must set the newly
created GHCR package `energy-prices-manager` to **Public** in GitHub package
settings. Home Assistant installations must be able to pull the generic image
without a GitHub login.

### GitHub repository settings

Keep both **Releases** and **Packages** enabled for this repository:

- **Releases** are used by Release Drafter for draft notes and by the Publish
  Release workflow for the final versioned release and Git tag.
- **Packages** enables the public GHCR image that Home Assistant downloads.

They are complementary. Do not delete a published release just to manage its
container image; deleting a release does not remove its Git tag, while release
notes rely on the release history for a useful comparison range.

For local checks, run:

```sh
uv sync
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest
```

## Support

- [GitHub Issues](https://github.com/hunter-nl/HA-Energy-Prices-Manager/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" height="50"></a>
