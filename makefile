.PHONY: run run-gs-usb build build-dmg build-appimage install-linux-desktop clean install format analyze
run:
	uv run python main.py

run-gs-usb:
	uv run python main.py -c gs_usb

build:
	uv run --group build python scripts/build_nuitka.py --clean

build-dmg:
	uv run --group build python scripts/build_nuitka.py --clean --dmg

build-appimage:
	uv run --group build python scripts/build_nuitka.py --clean --appimage

install-linux-desktop:
	scripts/install_linux_desktop.sh

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache dist build .venv

install:
	uv sync --all-groups

format:
	uv run --group dev ruff format .
	uv run --group dev ruff check --fix .

analyze:
	uv run --group dev ruff format --check .
	uv run --group dev ruff check .
	uv run --group dev ty check .
	uv run --group dev mypy .
