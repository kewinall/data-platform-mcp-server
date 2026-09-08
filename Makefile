.PHONY: install lint test run run-http docker

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check src tests

test:
	pytest

run:
	DPMCP_TRANSPORT=stdio data-platform-mcp

run-http:
	DPMCP_TRANSPORT=streamable-http data-platform-mcp

docker:
	docker compose up --build
