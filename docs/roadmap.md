# Roadmap / 開發路線

## v0.1 — Foundation ✅
- MCP Python SDK v2
- stdio / Streamable HTTP
- Demo catalog + DataOps tools
- PostgreSQL read-only catalog adapter
- CI / security scan

## v0.2 — DataOps Integration ✅
- Airflow 3 public REST API read-only adapter
- OpenSearch ETL log search
- Grafana Loki ETL log search
- MCP resources and prompts
- Protocol-level in-memory MCP integration tests

## v0.3 — Enterprise Data Platform ✅
- Official `vertica-python` catalog adapter
- PostgreSQL + Vertica composite catalog routing
- Table metadata and projection metadata
- Vertica view lineage via `v_catalog.view_tables`
- SQLGlot SQL lineage extraction
- Parser/AST-based read-only SQL policy
- MCP SDK bearer-token authentication
- RBAC scopes and roles
- Structured audit JSONL
- CI/Security-gated tag + GitHub Release automation

## v0.4 — Production Delivery
- Kubernetes + Helm
- OIDC / Keycloak / Entra integration
- Multi-tenancy and tenant-aware RBAC
- OpenTelemetry metrics/traces
- External Secrets examples
- NetworkPolicy and Pod Security examples
- Offline / air-gapped deployment bundle
