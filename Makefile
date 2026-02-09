.PHONY: venv test npe-serve lint install

venv:
	python -m venv venv
	. venv/bin/activate && pip install -e .
	. venv/bin/activate && pip install pytest pytest-cov black flake8

test:
	pytest -q

npe-serve:
	python -m npe.api.server

install:
	pip install -e .

lint:
	black --check .
	flake8 .
