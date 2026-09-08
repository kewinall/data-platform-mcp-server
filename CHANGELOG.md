# Changelog

## v0.3.0 — 2026-09-09

### Added
- Official `vertica-python` read-only Vertica catalog adapter.
- Vertica schema/table/view discovery, metadata, projection metadata, lightweight row statistics, and `EXPLAIN`.
- Vertica `v_catalog.view_tables` lineage discovery.
- Composite catalog routing for PostgreSQL + Vertica through `DPMCP_MODE=multi`.
- SQLGlot AST-based read-only SQL policy and SQL lineage extraction.
- MCP tools: `whoami`, `get_table_metadata`, `get_table_lineage`, and `analyze_sql_lineage`.
- MCP SDK v2 bearer-token authentication for Streamable HTTP.
- RBAC roles and per-tool scopes: reader, analyst, operator, and admin.
- Structured JSONL audit events with actor, role, action, outcome, latency, and redacted metadata.
- v0.3 security, Vertica, auth, audit, lineage, and protocol regression tests.

### Changed
- Release automation now waits until both CI and Security succeed for the same commit.
- Catalog resources now return governed table metadata rather than only column descriptions.
- PostgreSQL view lineage is derived from `information_schema.views` with SQLGlot.
- Health/capabilities report version 0.3.0 and metadata/lineage/SQL-policy capabilities.

### Security
- Vertica connections issue `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`.
- SQL audit records store a fingerprint instead of raw SQL text.
- Bearer tokens are validated by the MCP SDK HTTP authorization layer and are never audit fields.

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
