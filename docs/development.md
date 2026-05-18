# Development Guide

This guide covers the maintenance workflow for CANViewer.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- `make` is optional, but the Makefile mirrors the common commands

Install the full development environment:

```bash
uv sync --all-groups
```

Run the application:

```bash
uv run python main.py
```

Run with a gs_usb-compatible CAN device:

```bash
uv run python main.py -c gs_usb
```

## Checks

Run all local static checks:

```bash
make analyze
```

Equivalent commands:

```bash
uv run --group dev ruff format --check .
uv run --group dev ruff check .
uv run --group dev ty check .
uv run --group dev mypy .
```

Format and apply safe lint fixes:

```bash
make format
```

Equivalent commands:

```bash
uv run --group dev ruff format .
uv run --group dev ruff check --fix .
```

`ty` is currently run alongside `mypy`. Keep both until `ty` has proven stable for this codebase.

## Dependency Updates

Update all locked dependencies:

```bash
uv lock --upgrade
uv sync --locked --all-groups
```

Then run:

```bash
make analyze
uv run --group build python scripts/build_nuitka.py --help
```

When updating dependencies, watch for Python version constraints. For example, `returns` 0.27 requires Python 3.11 or newer, so the project currently uses `requires-python = ">=3.11,<3.14"`.

## Nuitka Builds

Local build commands:

```bash
make build
make build-dmg
make build-appimage
```

Platform outputs:

- macOS: `dist/CANViewer.app`, optionally `dist/CANViewer.dmg`
- Linux: `dist/CANViewer-<arch>.AppImage`
- Windows: `dist/CANViewer.exe`

The shared build entrypoint is:

```bash
uv run --group build python scripts/build_nuitka.py --clean
```

Useful options:

- `--dmg`: create a macOS DMG after building the app bundle
- `--appimage`: create a Linux AppImage after building the standalone app

## Linux Desktop Entry

After building an AppImage, install it into the user profile and register a desktop entry:

```bash
make install-linux-desktop
```

This installs into:

- `~/.local/bin/CANViewer.AppImage`
- `~/.local/share/applications/com.tomixrm.CANViewer.desktop`
- `~/.local/share/icons/hicolor/256x256/apps/CANViewer.png`

## GitHub Actions

The release workflow supports two modes:

- `workflow_dispatch`: build and upload artifacts only
- `v*.*.*` tag push: build artifacts and create a GitHub Release

The release job is guarded so manual runs do not publish releases:

```yaml
if: startsWith(github.ref, 'refs/tags/v')
```

Use manual dispatch to test the full build matrix before cutting a release tag.

## Release Checklist

1. Run local checks with `make analyze`.
2. Run a manual GitHub Actions build from the target branch.
3. Inspect uploaded artifacts for all platforms.
4. Create and push a release tag, for example:

   ```bash
   git tag v0.0.10
   git push origin v0.0.10
   ```

5. Confirm the GitHub Release contains:
   - `CANViewer-*.AppImage`
   - `CANViewer.exe`
   - `CANViewer.dmg`
