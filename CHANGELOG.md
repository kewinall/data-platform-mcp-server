# Changelog

## v0.2.0 — 2026-09-08

### Added
- Read-only Airflow 3 public REST API adapter using `/api/v2`.
- OpenSearch ETL log search adapter.
- Grafana Loki `query_range` log search adapter.
- Independently selectable catalog, orchestration, and log backends.
- MCP resources for platform capabilities and table catalog entries.
- MCP prompts for DataOps incident triage and data discovery.
- In-memory MCP protocol integration tests using the official Python SDK client.
- Integration documentation and v0.2 release guide.

### Changed
- Split orchestration and log-search adapter responsibilities.
- Health/capabilities report version 0.2.0.

## v0.1.0 — 2026-09-08

### Added
- MCP Python SDK v2 server with stdio and Streamable HTTP transports.
- 11 Data Engineering / DataOps MCP tools.
- Synthetic demo catalog, DAG, ETL log, and runbook data.
- PostgreSQL read-only catalog adapter.
- SQL write/DDL guardrails and statement timeout.
- Docker, Docker Compose, pytest, Ruff, pip-audit, and Trivy workflows.
- Traditional Chinese / English documentation.
