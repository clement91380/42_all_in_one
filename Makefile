.PHONY: install dev test clean gui server

install:
	./install.sh

dev:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

test:
	. .venv/bin/activate && python -m pytest tests/ -v

gui:
	. .venv/bin/activate && python -m forty_two_aio.main --gui

server:
	. .venv/bin/activate && naf server

clean:
	rm -rf build/ dist/ *.egg-info .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
