# Data Platform MCP Server

**目前版本 / Current release: v0.1.0**

> **繁體中文**：這是一個面向 Data Engineering / DataOps 的 Model Context Protocol (MCP) Server 參考專案，讓 ChatGPT、Claude、Codex 或其他 MCP Host 能以標準 Tool 介面查詢資料平台的 Schema、Table、統計資訊、SQL Explain、DAG 狀態、ETL Log 與 Runbook。
>
> **English**: A production-oriented Model Context Protocol (MCP) server reference for Data Engineering and DataOps. It exposes schema discovery, table metadata, lightweight statistics, SQL explain plans, DAG state, ETL logs, and runbook search as standardized MCP tools.

> **繁體中文**：Repository 預設只使用 synthetic demo data，不包含任何公司、客戶、真實資料庫帳密、內部 URL 或正式環境資訊。
>
> **English**: The repository defaults to synthetic demo data and contains no company/customer data, real credentials, internal URLs, or production environment information.

## v0.1 重點 / v0.1 Highlights

- Official MCP Python SDK v2 (`MCPServer`)
- stdio and Streamable HTTP transports
- 11 MCP tools for catalog, SQL, DataOps, logs, and runbooks
- Synthetic zero-dependency demo mode
- Optional read-only PostgreSQL catalog adapter
- SQL read-only guardrails
- Docker / Docker Compose
- pytest + Ruff CI
- pip-audit + Trivy security workflow
- Bilingual Traditional Chinese / English documentation

## 架構 / Architecture

```text
ChatGPT / Claude / Codex / MCP Host
                |
                | MCP (stdio / Streamable HTTP)
                v
      +---------------------------+
      | Data Platform MCP Server  |
      |       MCPServer v2        |
      +-------------+-------------+
                    |
        +-----------+------------+
        |           |            |
        v           v            v
   Catalog      Operations    Runbooks
   Adapter       Adapter       Adapter
        |           |            |
   Demo/Postgres  Demo(*)    Synthetic docs
        |
        v
 Schema / Table / Statistics / EXPLAIN
```

`(*)` Airflow REST adapter is scaffolded in v0.1; production activation and centralized log backends are planned for later releases.

## MCP Tools

| Tool | Purpose / 用途 |
|---|---|
| `health` | Server health and version / 服務健康狀態 |
| `list_data_sources` | List configured sources / 列出資料來源 |
| `list_schemas` | List schemas / 列出 Schema |
| `list_tables` | List tables/views / 列出 Table/View |
| `describe_table` | Column metadata / 欄位資訊 |
| `table_statistics` | Lightweight statistics / 輕量統計 |
| `explain_sql` | Read-only SQL explain / 唯讀 SQL 執行計畫 |
| `list_dags` | List orchestration DAGs / DAG 清單 |
| `get_dag_status` | Latest DAG state / DAG 狀態 |
| `search_etl_logs` | Search ETL logs / ETL Log 搜尋 |
| `search_runbooks` | Search operations knowledge / Runbook 搜尋 |

## 快速開始 / Quick Start

### Python

```bash
git clone https://github.com/kewinall/data-platform-mcp-server.git
cd data-platform-mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

Run with stdio:

```bash
DPMCP_TRANSPORT=stdio data-platform-mcp
```

Run with Streamable HTTP:

```bash
DPMCP_TRANSPORT=streamable-http data-platform-mcp
```

Default MCP endpoint:

```text
http://localhost:8000/mcp
```

### Docker

```bash
cp .env.example .env
docker compose up --build
```

## PostgreSQL Read-only Mode

```bash
export DPMCP_MODE=postgres
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@db:5432/analytics'
data-platform-mcp
```

**安全原則 / Security principles**

1. Use a database account with SELECT/catalog permissions only.
2. `default_transaction_read_only=on` is set on PostgreSQL sessions.
3. The MCP tool rejects write/DDL SQL and multiple statements.
4. Statement timeout is enabled.
5. No business rows are returned by `table_statistics`; planner estimates are used.

Application guardrails are defense-in-depth and do **not** replace database-side least privilege.

## Development

```bash
make install
make lint
make test
```

## CI / Security

CI validates:

```text
ruff check src tests
pytest
python -m compileall -q src
```

Security workflow:

- `pip-audit`
- Trivy filesystem scan (CRITICAL/HIGH)

## Roadmap

- **v0.1**: MCP protocol, demo catalog, PostgreSQL read-only adapter, DataOps demo tools
- **v0.2**: Airflow 3 REST integration, OpenSearch/Loki log search, resource/prompt support
- **v0.3**: Vertica adapter, metadata/lineage, RBAC/API token policy, audit logging
- **v0.4**: Kubernetes/Helm, OIDC, multi-tenancy, observability, offline deployment

## Documentation

- `docs/architecture.md` — 架構 / Architecture
- `docs/tool-catalog.md` — MCP Tool Catalog
- `docs/installation.md` — 安裝 / Installation
- `docs/security.md` — Security Design
- `docs/roadmap.md` — Roadmap
- `CHANGELOG.md` — Release notes

## License

MIT License. See `LICENSE`.
