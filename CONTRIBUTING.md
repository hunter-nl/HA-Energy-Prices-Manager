# Contributing Guidelines

## Local development

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) tool.
2. Install project dependencies using `uv sync` command.
3. Run the integration locally using `./scripts/run` script and open the UI at <http://localhost:8123>
4. Configure the integration using the Home Assistant UI.

## Testing

Run all tests:

```bash
uv run pytest
```

Run a single test:

```bash
uv run pytest --cov-fail-under=0 tests/test_init.py
```

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository** on GitHub
2. **Create a feature or fix branch** from `main` for your work:
   ```bash
   git checkout -b feature/my-feature
   # or for a bug fix:
   git checkout -b fix/my-bugfix
   ```
3. **Make your changes** in your created branch and test them locally
4. **Commit your changes** with clear commit messages:
   ```bash
   git commit -m "feat: add new feature"
   # or
   git commit -m "fix: resolve issue #123"
   ```
5. **Push your branch** to your fork:
   ```bash
   git push origin feature/my-feature
   # or
   git push origin fix/my-bugfix
   ```
6. **Open a Pull Request** against the `main` branch of the original repository
   - Describe your changes in the PR description
   - Reference any related issues
   - Ensure all tests pass locally before submitting

The repository owner will review your PR and merge it if appropriate.

## License

By contributing, you agree that your contributions will be licensed under its GNU AFFERO GENERAL PUBLIC LICENSE Version 3 License.

## Funding

If you find this project useful, consider supporting its development:

<a href="https://www.buymeacoffee.com/hunter.nl" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>