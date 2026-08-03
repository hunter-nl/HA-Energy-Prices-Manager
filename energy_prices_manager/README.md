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

Manage electricity and gas tariff periods from Home Assistant. The app keeps
the current-price helpers up to date automatically at startup, at midnight,
and whenever you save a period.

Install the app, start it, then open **Energy Prices Manager** from the sidebar
to add or update tariff periods. The app creates electricity import T1/T2,
electricity export T1/T2, and gas price helpers when it starts. Electricity
prices can be positive or negative; a positive export price is compensation,
while a negative one is a charge for exporting power to the grid.

For usage, installation, and troubleshooting, see the repository
[documentation](../README.md).

## Support

- [GitHub Issues](https://github.com/hunter-nl/HA-Energy-Prices-Manager/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" height="50"></a>
