# Data Platform MCP Server

**目前版本：v0.5.0**

> **互動式架構與專案總覽**  
> [GitHub Pages](https://kewinall.github.io/data-platform-mcp-server/) · [Repository HTML](docs/data-platform-mcp-server-guide.html)

這是一套 production-oriented **Tool / Integration Layer**，將 PostgreSQL、Vertica、Airflow、logs、metadata、lineage 與 normalized ETL metadata，透過受治理的 Model Context Protocol（MCP）tools 提供給 AI Agent、IDE 與 MCP Host。

預設使用 synthetic demo data，不需要公司 / 客戶資料、真實 credential 或 internal URL。

## 專案定位

本 Repository 負責 Portfolio 中的 **Canonical MCP Access Layer**：

- MCP protocol transport 與 tool contracts
- PostgreSQL / Vertica catalog access
- read-only SQL guardrails
- Airflow 與 log integrations
- metadata 與 lineage access
- OIDC/JWT authentication
- RBAC 與 per-tool scopes
- tenant-aware source isolation
- structured audit events
- OpenTelemetry observability
- 消費 `enterprise-etl-platform` 產生的 normalized ETL metadata

本專案刻意不實作 autonomous agent orchestration、RAG chat、model routing，或 ETL parsing / migration truth。

## 架構

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

## 核心能力

- MCP SDK v2 / Streamable HTTP
- PostgreSQL + Vertica catalog adapters
- multi-source catalog abstraction
- metadata 與 table / projection inspection
- catalog-backed 與 SQL AST lineage
- SQLGlot-based read-only SQL policy
- database read-only session enforcement
- Airflow 3 `/api/v2` integration
- OpenSearch / Loki log search
- OIDC/JWT + JWKS validation
- roles：`reader`、`analyst`、`operator`、`admin`
- per-tool scopes
- tenant-aware source isolation
- structured audit JSONL
- Kubernetes Helm deployment
- NetworkPolicy / PDB / optional HPA
- External Secrets examples
- OpenTelemetry traces + metrics
- air-gapped bundle support

## ETL Metadata Contract

`enterprise-etl-platform` 是 ETL metadata 與 lineage truth 的 producer；本 Server 只消費已發布的 normalized artifacts。

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

MCP layer 會保留 producer 的 `structural`、`inferred-deterministic` 與 capability boundary 等分類，不會自行補出缺失的 lineage。

## 關鍵工程決策

| 決策 | 原因 / 效益 | Trade-off |
|---|---|---|
| MCP Tool Contract 作為 integration boundary | Client 使用受治理 capability，而不是直接取得 raw backend credentials / APIs | 增加 protocol / schema compatibility 維護成本 |
| Adapter Pattern 隔離 platform backends | Tool contract 穩定，backend 可獨立替換 | Backend-specific behavior 仍需在 adapter 層維護 |
| Read-only by design + AST policy + DB session | 安全控制位於 prompt 之下，形成 defense in depth | 保守 policy 可能拒絕部分複雜但合法的 SQL |
| RBAC 決定 what，tenant policy 決定 which source | operation authorization 與 data-source isolation 分離 | Source-level tenant isolation 不等同 row-level RLS |
| OIDC/JWT 在 resource boundary 驗證 | 集中處理 identity 與 role mapping | IdP / JWKS availability 成為 auth dependency |
| Producer-owned ETL metadata contract | 避免 parser / lineage truth 被複製成第二套 | 需要維護 schema / version compatibility |

## 失敗語意與復原原則

- malformed 或 mutation-capable SQL 在 database execution 前直接拒絕
- cross-tenant source access 直接 deny，不 fallback 到 unrestricted access
- OIDC / JWKS 驗證失敗時 fail closed
- backend outage 回傳 bounded tool failure，不升高權限
- invalid ETL metadata artifact fail closed
- lineage 缺失時維持缺失，不由 MCP Server fabricate edge

## 可驗證 Evidence

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

## 快速開始

```bash
git clone https://github.com/kewinall/data-platform-mcp-server.git
cd data-platform-mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

stdio：

```bash
DPMCP_TRANSPORT=stdio data-platform-mcp
```

HTTP：

```bash
DPMCP_TRANSPORT=streamable-http data-platform-mcp
```

Endpoint：`http://127.0.0.1:8000/mcp`

## 主要 Tools

| Tool | Scope | 用途 |
|---|---|---|
| `health` | `platform:read` | health / version |
| `whoami` | `platform:read` | identity、role、tenant、scopes |
| `list_data_sources` | `catalog:read` | tenant-visible sources |
| `describe_table` | `catalog:read` | column metadata |
| `get_table_lineage` | `lineage:read` | catalog lineage |
| `analyze_sql_lineage` | `lineage:read` | SQL AST lineage |
| `explain_sql` | `sql:explain` | guarded EXPLAIN |
| `list_dags` | `operations:read` | Airflow DAG discovery |
| `search_etl_logs` | `logs:read` | ETL log search |
| `list_etl_pipelines` | `catalog:read` | normalized ETL pipeline discovery |
| `get_etl_table_lineage` | `lineage:read` | producer lineage + capability boundary |

## 工程文件

`docs/` 內包含 OIDC、MCP protocol、ETL metadata integration、deployment、observability、security 與 operational guidance。

## Portfolio 責任邊界

- **Data Platform MCP Server**：standardized governed tool / integration access
- **Enterprise ETL Platform**：ETL metadata producer、migration truth、lineage truth
- **Agentic DataOps Copilot**：operational reasoning client
- **Enterprise RAG Platform**：enterprise knowledge 與 retrieval
- **Multi-LLM AI Gateway**：model control plane

## 授權

MIT
