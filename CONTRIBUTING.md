# Contributing Guidelines

Energy Prices Manager is a Home Assistant App, not a custom integration. The
App source is self-contained in `energy_prices_manager/`; it includes the
Dockerfile, FastAPI backend, Ingress frontend, configuration, and branding.

## Local development

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Run `uv sync`.
3. Run the quality checks below before opening a pull request.

To test the full App in Home Assistant, copy the
`energy_prices_manager` directory to `/addons/local/energy_prices_manager`,
temporarily comment out its `image:` setting, refresh the App Store, then
install it. This tells Supervisor to build the local Dockerfile.

## Testing

Run the complete suite:

```sh
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest
```

Run a single test file:

```sh
uv run pytest tests/test_main.py
```

When changing `energy_prices_manager/config.yaml`, the Dockerfile, or a release
workflow, also validate the YAML and release configuration:

```sh
ruby -e 'require "yaml"; YAML.load_file("energy_prices_manager/config.yaml"); YAML.load_file(".github/workflows/publish-release.yaml")'
git-cliff --config .github/.git-cliff.toml --unreleased --tag vX.Y.Z --strip all --offline
```

## Pull requests

1. Fork the repository and create a `feature/`, `fix/`, `docs/`, or `chore/`
   branch from `main`.
2. Keep the change focused and update tests or documentation when behaviour
   changes.
3. Use a concise Conventional Commit message, such as `fix(app): ...`.
4. Open a pull request against `main` with the validation you ran.

The release workflow is version-driven: **Prepare release** updates the App
configuration, Python metadata, and changelog in a release PR. Merging that PR
builds and publishes the `amd64` and `aarch64` GHCR images, combines them into
a generic manifest, and creates the GitHub Release. Do not manually create
release tags or release zip files.

## License

By contributing, you agree that your contributions are licensed under the GNU
Affero General Public License v3.0.

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
