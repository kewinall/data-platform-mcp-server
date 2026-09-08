.PHONY: install lint test run run-http docker platform-check airgap

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

platform-check:
	bash -n scripts/*.sh
	helm lint deploy/helm/data-platform-mcp-server -f tests/helm-values.yaml
	helm template dpmcp deploy/helm/data-platform-mcp-server -f tests/helm-values.yaml >/dev/null

airgap:
	bash scripts/build-airgap-bundle.sh
