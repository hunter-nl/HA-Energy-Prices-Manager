# AGENTS.md

## Project Overview

Energy Prices Manager is a Home Assistant App for maintaining electricity and
gas tariff periods. It is distributed through a Home Assistant App repository
and GHCR multi-architecture images; it is not a HACS custom integration.

## Setup Commands

- Install dependencies: `uv sync`
- Run all checks: `uv run ruff check && uv run ruff format --check && uv run ty check && uv run pytest`
- Run tests: `uv run pytest`
- Run linter: `uv run ruff check`
- Run type checker: `uv run ty check`
- Format code: `uv run ruff format`

## App Structure

- `energy_prices_manager/config.yaml`: Supervisor App metadata, supported
  architectures, Ingress, and GHCR image name.
- `energy_prices_manager/Dockerfile`: the single source of truth for App and
  OCI image metadata, build arguments, and runtime dependencies.
- `energy_prices_manager/app/main.py`: FastAPI API, period persistence, and
  Home Assistant helper creation/synchronisation.
- `energy_prices_manager/web/`: Ingress frontend assets.
- `repository.yaml`: Home Assistant App repository metadata.

## Release and Distribution

- Keep GitHub **Releases** and **Packages** enabled. Releases provide draft and
  final notes; Packages hosts the public GHCR App image.
- The manually entered Prepare Release version is authoritative. It must match
  `energy_prices_manager/config.yaml` and published image tags.
- Publish Release builds `amd64` and `aarch64` images with the maintained Home
  Assistant Builder actions, then publishes the generic multi-architecture
  manifest `ghcr.io/hunter-nl/energy-prices-manager:<version>`.
- Do not create zip release artifacts, manually create release tags, or add
  `{arch}` to the public `image:` configuration.

## General Rules

- Use GitHub tooling for repository, issue, and pull-request work.
- Use current official Home Assistant App documentation when changing App
  configuration, Docker image publishing, or Supervisor communication.
- Comments should be sparse and explain why, not what.
- Preserve the Energy Dashboard helper IDs and English helper names.
- Keep changes maintainable, testable, and focused. Add or update tests when
  backend behaviour changes.
