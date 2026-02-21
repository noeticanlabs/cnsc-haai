.PHONY: venv test npe-serve lint install

venv:
	python -m venv venv
	. venv/bin/activate && pip install -e .
	. venv/bin/activate && pip install pytest pytest-cov black flake8

test:
	PYTHONPATH=./src pytest -q

npe-serve:
	PYTHONPATH=./src python -m npe.api.server

install:
	pip install -e .

lint:
	black --check .
	flake8 .
