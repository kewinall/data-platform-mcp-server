# Data Platform MCP Server

**目前版本 / Current release: v0.2.0**

> **繁體中文**：這是一個面向 Data Engineering / DataOps 的 Model Context Protocol (MCP) Server 參考專案，讓 ChatGPT、Claude、Codex 或其他 MCP Host 能以標準 MCP Tool、Resource、Prompt 介面安全地查詢資料平台。
>
> **English**: A production-oriented Model Context Protocol (MCP) server reference for Data Engineering and DataOps. It exposes data-platform capabilities through standardized MCP tools, resources, and prompts.

> **繁體中文**：Repository 預設只使用 synthetic demo data，不包含任何公司、客戶、真實資料庫帳密、內部 URL 或正式環境資訊。
>
> **English**: The repository defaults to synthetic demo data and contains no company/customer data, real credentials, internal URLs, or production environment information.

## v0.2 重點 / v0.2 Highlights

- Official MCP Python SDK v2 (`MCPServer`)
- stdio and Streamable HTTP transports
- 11 MCP tools for catalog, SQL, DataOps, logs, and runbooks
- MCP resources + resource templates
- MCP prompts for incident triage and data discovery
- Synthetic zero-dependency demo mode
- Optional read-only PostgreSQL catalog adapter
- Airflow 3 stable public REST API (`/api/v2`) adapter
- OpenSearch ETL log search
- Grafana Loki ETL log search
- SQL read-only guardrails
- Docker / Docker Compose
- Protocol-level MCP tests + pytest + Ruff CI
- pip-audit + Trivy security workflow
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
        +-----------+-------------+----------------+
        |                         |                |
        v                         v                v
  Catalog Adapter          Operations Adapter   Log Adapter
  Demo / PostgreSQL        Demo / Airflow 3    Demo/OpenSearch/Loki
        |                         |                |
        +-------------------------+----------------+
                                  |
                                  v
                         Runbook Knowledge
```

## MCP Primitives

### Tools

| Tool | Purpose / 用途 |
|---|---|
| `health` | Server health and version / 服務健康狀態 |
| `list_data_sources` | List configured sources / 列出資料來源 |
| `list_schemas` | List schemas / 列出 Schema |
| `list_tables` | List tables/views / 列出 Table/View |
| `describe_table` | Column metadata / 欄位資訊 |
| `table_statistics` | Lightweight statistics / 輕量統計 |
| `explain_sql` | Read-only SQL explain / 唯讀 SQL 執行計畫 |
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

Docker:

```bash
cp .env.example .env
docker compose up --build
```

## Production Adapter Example

```bash
export DPMCP_MODE=postgres
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@db:5432/analytics'

export DPMCP_OPERATIONS_MODE=airflow
export DPMCP_AIRFLOW_BASE_URL='https://airflow.example.internal'
export DPMCP_AIRFLOW_TOKEN='replace-me'

export DPMCP_LOGS_MODE=loki
export DPMCP_LOKI_URL='https://loki.example.internal'
export DPMCP_LOKI_TOKEN='replace-me'

data-platform-mcp
```

See `docs/integrations.md`.

## Security Principles

1. All v0.2 platform integrations are read-only.
2. Use backend identities with minimum read permissions only.
3. PostgreSQL sessions enable `default_transaction_read_only=on`.
4. SQL write/DDL and multiple statements are rejected.
5. Airflow adapter uses GET endpoints only; it never triggers or clears DAGs.
6. OpenSearch adapter only searches indexes.
7. Loki adapter only uses `query_range`.
8. Secrets are supplied through environment variables and are not committed.

Application guardrails are defense-in-depth and do **not** replace backend-side least privilege.

## Development

```bash
make install
make lint
make test
```

CI validates Python 3.11/3.12, Ruff, pytest, compile, and Docker build. Security workflow runs pip-audit and Trivy.

## Roadmap

- **v0.1** ✅ MCP foundation + PostgreSQL read-only adapter
- **v0.2** ✅ Airflow 3 + OpenSearch/Loki + MCP Resources/Prompts
- **v0.3** Vertica + metadata/lineage + parser-based SQL policy + RBAC/API token + audit
- **v0.4** Kubernetes/Helm + OIDC/multi-tenancy + OpenTelemetry + offline deployment

## Documentation

- `docs/architecture.md` — 架構 / Architecture
- `docs/tool-catalog.md` — MCP Tool Catalog
- `docs/installation.md` — 安裝 / Installation
- `docs/integrations.md` — Airflow / OpenSearch / Loki
- `docs/security.md` — Security Design
- `docs/v0.2.md` — v0.2 Release Guide
- `docs/roadmap.md` — Roadmap
- `CHANGELOG.md` — Release notes

## License

MIT License. See `LICENSE`.
