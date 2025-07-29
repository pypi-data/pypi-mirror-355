# Release Process for aluna-cli

This document describes how to build and release new versions of aluna-cli to PyPI.

## Quick Release

The easiest way to release a new version:

```bash
# For a patch release (0.1.4 → 0.1.5)
make release-patch

# For a minor release (0.1.4 → 0.2.0)
make release-minor

# For a major release (0.1.4 → 1.0.0)
make release-major
```

## Manual Release Process

If you prefer to run the steps manually:

1. **Run linting checks**:
   ```bash
   make lint
   ```

2. **Update version** in `pyproject.toml`

3. **Build the package**:
   ```bash
   make build
   ```

4. **Upload to PyPI**:
   ```bash
   uv run twine upload dist/*
   ```

## Using the Release Scripts

### Python Script (build_and_release.py)

The main release script that handles everything:

```bash
# Default patch release
uv run python build_and_release.py

# Specific version bump
uv run python build_and_release.py minor
```

Features:
- Automatic version bumping
- Linting checks
- Clean build
- Interactive confirmations
- PyPI upload

### Shell Script (release.sh)

Simple wrapper around the Python script:

```bash
./release.sh [major|minor|patch]
```

## Pre-release Checklist

Before releasing:
1. ✓ All changes committed
2. ✓ Code passes linting (`make lint`)
3. ✓ README.md is up to date
4. ✓ CHANGELOG updated (if maintained)

## Post-release

After releasing:
1. Test the new version: `uvx aluna-cli@latest --version`
2. Create a git tag: `git tag v0.1.4 && git push origin v0.1.4`
3. Update any documentation

## Troubleshooting

If the release fails:
- Check PyPI credentials are configured
- Ensure version number hasn't been used
- Run `make clean` and try again
- Check network connectivity to PyPI