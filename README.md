# Data Platform MCP Server

**目前版本 / Current release: v0.3.0**

> **繁體中文**：這是一個面向 Data Engineering / DataOps 的 Model Context Protocol (MCP) Server 參考專案，讓 ChatGPT、Claude、Codex 或其他 MCP Host 能以標準 MCP Tool、Resource、Prompt 介面安全地查詢資料平台。
>
> **English**: A production-oriented Model Context Protocol (MCP) server reference for Data Engineering and DataOps. It exposes data-platform capabilities through standardized MCP tools, resources, and prompts.

> **繁體中文**：Repository 預設只使用 synthetic demo data，不包含任何公司、客戶、真實資料庫帳密、內部 URL 或正式環境資訊。
>
> **English**: The repository defaults to synthetic demo data and contains no company/customer data, real credentials, internal URLs, or production environment information.

## v0.3 重點 / v0.3 Highlights

- Official MCP Python SDK v2 (`MCPServer`)
- stdio and Streamable HTTP transports
- PostgreSQL + Vertica catalog adapters
- Composite catalog mode for multiple database sources
- Vertica metadata, projections, lightweight statistics, and catalog-backed view lineage
- SQLGlot AST-based read-only SQL policy
- SQL lineage extraction for referenced tables and CTEs
- MCP bearer authentication over Streamable HTTP
- RBAC roles: `reader`, `analyst`, `operator`, `admin`
- Per-tool scopes such as `catalog:read`, `lineage:read`, `operations:read`, and `logs:read`
- Structured JSONL audit log with actor, role, action, outcome, and latency
- Airflow 3 stable public REST API (`/api/v2`) adapter
- OpenSearch / Grafana Loki ETL log search
- Docker / Docker Compose
- Protocol-level MCP tests + pytest + Ruff CI
- pip-audit + Trivy security workflow
- CI/Security-gated automatic Git tag + GitHub Release
- Traditional Chinese / English documentation

## 架構 / Architecture

```text
ChatGPT / Claude / Codex / MCP Host
                |
        MCP (stdio / HTTP)
                |
                v
      +---------------------------+
      | Data Platform MCP Server  |
      |       MCPServer v2        |
      +-------------+-------------+
                    |
          Auth / RBAC / Audit
                    |
        +-----------+-------------+----------------+
        |                         |                |
        v                         v                v
  Catalog Adapter          Operations Adapter   Log Adapter
 Demo/Postgres/Vertica       Demo / Airflow 3   Demo/OpenSearch/Loki
        |
        +--> Metadata / Lineage
        +--> SQLGlot AST policy
```

## MCP Tools

| Tool | Purpose / 用途 |
|---|---|
| `health` | Server health/version / 服務健康狀態 |
| `whoami` | Effective caller identity/RBAC / 呼叫者身分與角色 |
| `list_data_sources` | List configured sources / 列出資料來源 |
| `list_schemas` | List schemas / 列出 Schema |
| `list_tables` | List tables/views / 列出 Table/View |
| `describe_table` | Column metadata / 欄位資訊 |
| `table_statistics` | Lightweight statistics / 輕量統計 |
| `get_table_metadata` | Governed metadata / 物件類型、Owner、Projection 等 |
| `get_table_lineage` | Catalog-backed lineage / Catalog 血緣 |
| `analyze_sql_lineage` | SQL AST lineage / SQL 輸入表與 CTE 血緣 |
| `explain_sql` | Guarded read-only EXPLAIN / 唯讀 SQL 執行計畫 |
| `list_dags` | List Airflow/demo DAGs / DAG 清單 |
| `get_dag_status` | Latest DAG state / DAG 狀態 |
| `search_etl_logs` | Demo/OpenSearch/Loki log search / ETL Log 搜尋 |
| `search_runbooks` | Operations knowledge / Runbook 搜尋 |

### Resources

- `platform://capabilities`
- `catalog://{source}/{schema}/{table}`

### Prompts

- `incident_triage(dag_id, symptom)`
- `data_discovery(source, schema, question)`

## 快速開始 / Quick Start

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

Streamable HTTP:

```bash
DPMCP_TRANSPORT=streamable-http data-platform-mcp
```

Default MCP endpoint:

```text
http://localhost:8000/mcp
```

## PostgreSQL + Vertica Multi-source Example

```bash
export DPMCP_MODE=multi
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@postgres:5432/analytics'
export DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@vertica:5433/warehouse?tlsmode=require'

data-platform-mcp
```

The server exposes both sources through the same MCP catalog API:

```text
postgres
vertica
```

## Bearer Auth + RBAC Example

Bearer auth is available for **Streamable HTTP**. The MCP SDK verifies the `Authorization: Bearer ...` header before tools run.

```bash
export DPMCP_TRANSPORT=streamable-http
export DPMCP_AUTH_ENABLED=true
export DPMCP_AUTH_ISSUER_URL='https://auth.example.com'
export DPMCP_AUTH_RESOURCE_URL='http://127.0.0.1:8000/mcp'
export DPMCP_API_TOKENS_JSON='{
  "replace-reader-token":{"client_id":"catalog-agent","role":"reader"},
  "replace-ops-token":{"client_id":"dataops-agent","role":"operator"}
}'

data-platform-mcp
```

Role model:

| Role | Core scopes |
|---|---|
| `reader` | platform/catalog/runbook read |
| `analyst` | reader + SQL explain + lineage |
| `operator` | analyst + Airflow + log search |
| `admin` | all current read-only scopes + audit scope |

`stdio` has no HTTP bearer layer. Its trust boundary is the local process that launches the server.

## Security Principles

1. No destructive MCP tool exists.
2. SQL is parsed by SQLGlot and only a single read-only query is accepted.
3. `SELECT ... INTO`, DML, DDL, transaction-changing commands, and multi-statements are rejected.
4. PostgreSQL sessions use `default_transaction_read_only=on`.
5. Vertica sessions execute `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`.
6. Database accounts must still be least-privileged; application policy is defense-in-depth.
7. Airflow adapter uses GET endpoints only.
8. OpenSearch/Loki adapters only perform read/search operations.
9. HTTP bearer authentication uses the MCP SDK authorization middleware.
10. Audit records never contain bearer tokens and store SQL fingerprints instead of raw SQL text.

## Audit

Default audit output is structured logging. Optional JSONL file output:

```bash
export DPMCP_AUDIT_ENABLED=true
export DPMCP_AUDIT_LOG_PATH=/var/log/data-platform-mcp/audit.jsonl
```

Example event:

```json
{
  "action": "sql.explain",
  "actor": "catalog-agent",
  "duration_ms": 8.421,
  "metadata": {"source": "vertica", "sql_fingerprint": "2e83b9f14c99b7e1"},
  "outcome": "success",
  "role": "analyst"
}
```

## CI / Release

CI validates Python 3.11/3.12, Ruff, pytest, compile, and Docker build. Security validates dependencies and filesystem vulnerabilities with pip-audit and Trivy.

A release is created only after **CI and Security are both successful for the same `main` commit**. The workflow reads the version from `pyproject.toml`, then creates the matching Git tag and GitHub Release.

## Roadmap

- **v0.1** ✅ MCP foundation + PostgreSQL read-only adapter
- **v0.2** ✅ Airflow 3 + OpenSearch/Loki + MCP Resources/Prompts
- **v0.3** ✅ Vertica + multi-source catalog + metadata/lineage + SQL AST policy + bearer RBAC + audit
- **v0.4** Kubernetes/Helm + OIDC/multi-tenancy + OpenTelemetry + External Secrets + offline deployment

## Documentation

- `docs/architecture.md` — 架構 / Architecture
- `docs/tool-catalog.md` — MCP Tool Catalog
- `docs/installation.md` — 安裝 / Installation
- `docs/integrations.md` — PostgreSQL / Vertica / Airflow / OpenSearch / Loki
- `docs/security.md` — Security / RBAC / Audit Design
- `docs/v0.2.md` — v0.2 Release Guide
- `docs/v0.3.md` — v0.3 Release Guide
- `docs/roadmap.md` — Roadmap
- `CHANGELOG.md` — Release notes

## License

MIT License. See `LICENSE`.
