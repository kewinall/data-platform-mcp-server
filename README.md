# Data Platform MCP Server

**Current release: v0.5.0**

> **Interactive architecture & project overview**  
> [Live GitHub Pages](https://kewinall.github.io/data-platform-mcp-server/) · [Repository HTML](docs/data-platform-mcp-server-guide.html)

Production-oriented **Tool / Integration Layer** for enterprise data platforms. It exposes PostgreSQL, Vertica, Airflow, logs, metadata, lineage, and normalized ETL metadata through governed Model Context Protocol (MCP) tools.

Synthetic demo data is used by default. No company/customer data, real credentials, or internal URLs are required.

## Engineering Scope

This repository owns the **canonical MCP access layer**:

- MCP protocol transport and tool contracts
- PostgreSQL and Vertica catalog access
- read-only SQL guardrails
- Airflow and log integrations
- metadata and lineage access
- OIDC/JWT authentication
- RBAC and per-tool scopes
- tenant-aware source isolation
- structured audit events
- OpenTelemetry observability
- normalized ETL metadata consumption from `enterprise-etl-platform`

It intentionally does not implement autonomous agent orchestration, RAG chat, model routing, or ETL parsing/migration truth.

## Architecture

```text
ChatGPT / Claude / Codex / MCP Host
                 |
                 | MCP Streamable HTTP
                 v
        +----------------------+
        | MCP SDK Bearer Gate  |
        | Static / OIDC JWT    |
        +----------+-----------+
                   |
             Role / Scope
                   |
             Tenant Policy
                   |
             Audit + OTel
                   |
        +----------v-----------+
        | DataPlatformService  |
        +-----+-----------+----+
              |           |
       Catalog layer   DataOps layer
              |           |
       +------+-----+     +----------------+
       |            |     |                |
 PostgreSQL      Vertica Airflow       Logs/Runbooks
```

## Core Capabilities

- MCP SDK v2 / Streamable HTTP
- PostgreSQL + Vertica catalog adapters
- multi-source catalog abstraction
- metadata and table/projection inspection
- catalog-backed and SQL AST lineage
- SQLGlot-based read-only SQL policy
- database read-only session enforcement
- Airflow 3 `/api/v2` integration
- OpenSearch / Loki log search
- OIDC/JWT + JWKS validation
- roles: `reader`, `analyst`, `operator`, `admin`
- per-tool scopes
- tenant-aware source isolation
- structured audit JSONL
- Kubernetes Helm deployment
- NetworkPolicy / PDB / optional HPA
- External Secrets examples
- OpenTelemetry traces + metrics
- air-gapped bundle support

## ETL Metadata Contract

`enterprise-etl-platform` is the producer of ETL metadata and lineage truth. This server only consumes published normalized artifacts.

```text
Enterprise ETL Platform
  parser / migration / lineage truth
              |
              | normalized artifact
              v
Data Platform MCP Server
  governed read-only access
              |
              v
AI Agent / IDE / MCP Host
```

The MCP layer preserves producer classifications such as `structural`, `inferred-deterministic`, and capability boundaries. It does not invent missing lineage.

## Key Engineering Decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| MCP Tool Contract as integration boundary | Clients use governed capabilities instead of raw backend credentials/APIs | Additional protocol/schema compatibility work |
| Adapter Pattern for platform backends | Tool contracts stay stable while backends vary | Backend-specific behavior still requires adapter maintenance |
| Read-only by design + AST policy + DB session | Safety is enforced below the prompt layer | Conservative policy can reject some complex valid SQL |
| RBAC for what, tenant policy for which source | Separates operation authorization from data-source isolation | Source-level tenant isolation is not row-level RLS |
| OIDC/JWT validation at resource boundary | Centralizes identity and role mapping | IdP/JWKS availability becomes an auth dependency |
| Producer-owned ETL metadata contract | Prevents parser/lineage truth from being duplicated | Requires schema/version compatibility management |

## Failure Semantics

- malformed or mutation-capable SQL is rejected before database execution
- cross-tenant source access is denied instead of falling back to unrestricted access
- failed OIDC/JWKS verification fails closed
- backend outages return bounded tool failures without escalating privileges
- invalid ETL metadata artifacts fail closed
- missing lineage remains missing; the MCP server does not fabricate edges

## Production Evidence

| Claim | Repository Evidence |
|---|---|
| OIDC / RBAC / audit regression | `tests/test_auth_audit.py`, `tests/test_security.py`, `src/data_platform_mcp/security.py` |
| MCP protocol contract | `tests/test_mcp_protocol.py`, `tests/test_service.py` |
| PostgreSQL / Vertica boundary | `tests/test_vertica.py`, `tests/test_integrations.py` |
| Observability / audit correlation | `tests/test_observability.py`, `src/data_platform_mcp/observability.py`, `src/data_platform_mcp/audit.py` |
| Kubernetes baseline | `deploy/helm/data-platform-mcp-server/`, `tests/helm-values.yaml`, `.github/workflows/ci.yml` |
| Security gate | `.github/workflows/security.yml` |
| ETL metadata contract | `src/data_platform_mcp/adapters/etl_metadata.py`, `tests/test_etl_metadata.py` |
| ETL MCP integration | `tests/test_mcp_protocol.py`, `docs/etl-metadata-integration.md` |

## Quick Start

```bash
git clone https://github.com/kewinall/data-platform-mcp-server.git
cd data-platform-mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

stdio:

```bash
DPMCP_TRANSPORT=stdio data-platform-mcp
```

HTTP:

```bash
DPMCP_TRANSPORT=streamable-http data-platform-mcp
```

Endpoint: `http://127.0.0.1:8000/mcp`

## Selected Tools

| Tool | Scope | Purpose |
|---|---|---|
| `health` | `platform:read` | health/version |
| `whoami` | `platform:read` | identity, role, tenant, scopes |
| `list_data_sources` | `catalog:read` | tenant-visible sources |
| `describe_table` | `catalog:read` | column metadata |
| `get_table_lineage` | `lineage:read` | catalog lineage |
| `analyze_sql_lineage` | `lineage:read` | SQL AST lineage |
| `explain_sql` | `sql:explain` | guarded EXPLAIN |
| `list_dags` | `operations:read` | Airflow DAG discovery |
| `search_etl_logs` | `logs:read` | ETL log search |
| `list_etl_pipelines` | `catalog:read` | normalized ETL pipeline discovery |
| `get_etl_table_lineage` | `lineage:read` | producer lineage + capability boundary |

## Documentation

See `docs/` for OIDC, MCP protocol, ETL metadata integration, deployment, observability, security, and operational guidance.

## Portfolio Boundary

- **Data Platform MCP Server:** standardized governed tool/integration access
- **Enterprise ETL Platform:** ETL metadata producer, migration truth and lineage truth
- **Agentic DataOps Copilot:** operational reasoning client
- **Enterprise RAG Platform:** enterprise knowledge and retrieval
- **Multi-LLM AI Gateway:** model control plane

## License

MIT
