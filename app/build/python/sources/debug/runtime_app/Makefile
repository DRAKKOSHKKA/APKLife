.PHONY: install test lint run

install:
	python -m pip install -e .[dev]

test:
	pytest -q

lint:
	ruff check .
	black --check .
	mypy services routes app.py config.py

run:
	python app.py
