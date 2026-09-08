# Changelog

## v0.4.0 — 2026-09-09

### Added
- OIDC/JWT verification with JWKS for external identity providers such as Keycloak and Microsoft Entra ID.
- Configurable OIDC claim mapping for client ID, role, and tenant.
- Tenant-aware source isolation for PostgreSQL/Vertica catalog access.
- Tenant identity in `whoami`, audit events, and OpenTelemetry spans.
- OpenTelemetry traces and metrics with OTLP/HTTP export.
- Helm chart for Kubernetes production delivery.
- Restricted-style Kubernetes security contexts, non-root execution, read-only root filesystem, dropped Linux capabilities, and RuntimeDefault seccomp.
- NetworkPolicy with same-namespace ingress and explicit egress policy.
- PodDisruptionBudget and optional HorizontalPodAutoscaler.
- External Secrets Operator integration using `external-secrets.io/v1`.
- Azure Key Vault + Workload Identity SecretStore example.
- Kubernetes namespace example enforcing the Restricted Pod Security profile.
- OpenTelemetry Collector example.
- Air-gapped bundle build and checksum verification scripts.
- Helm chart validation in CI and rendered Kubernetes config scanning in Security workflow.
- Helm chart artifact attached automatically to GitHub Releases.

### Changed
- Health/capabilities report version 0.4.0 and production-delivery features.
- Release pipeline packages deployment artifacts after CI and Security gates pass.
- Docker runtime sets HOME to writable `/tmp` for read-only-root-filesystem Kubernetes deployments.
- Audit records now include tenant and trace correlation when available.

### Security
- OIDC access tokens are validated against issuer, audience, algorithm, expiration, signature, and subject.
- Unrecognized OIDC roles are rejected instead of receiving a default privileged role.
- Tenant policies deny access to unconfigured or unauthorized catalog sources.
- Helm defaults do not mount the Kubernetes ServiceAccount token.
- Helm defaults deny non-DNS egress until explicitly configured.

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

## v0.1.0 — 2026-09-08

### Added
- MCP Python SDK v2 server with stdio and Streamable HTTP transports.
- 11 Data Engineering / DataOps MCP tools.
- Synthetic demo catalog, DAG, ETL log, and runbook data.
- PostgreSQL read-only catalog adapter.
- SQL write/DDL guardrails and statement timeout.
- Docker, Docker Compose, pytest, Ruff, pip-audit, and Trivy workflows.
- Traditional Chinese / English documentation.
