.PHONY: run run-socketcan clean install format analyze

run:
uv run python main.py

run-socketcan:
uv run python main.py -c socketcan

clean:
rm -rf __pycache__ .mypy_cache .venv

install:
uv sync

format:
uv run black .

analyze:
uv run mypy .
