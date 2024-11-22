.PHONY: run run-socketcan clean install format
run:
	poetry run python main.py

run-socketcan:
	poetry run python main.py -c socketcan
clean:
	rm -rf __pycache__ .mypy_cache poetry.lock

install:
	poetry install

format:
	poetry run black .

analyze:
	poetry run mypy .