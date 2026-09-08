# Security Design / 安全設計

## Threat model / 威脅模型

The MCP server is an automation bridge between an LLM host and enterprise systems. A prompt mistake, prompt injection, or compromised MCP client must not automatically become a database or orchestrator write operation.

MCP Server 可能成為 LLM Host 與企業資料平台之間的自動化橋接層，因此安全設計必須假設 Prompt、Client 或上游資料可能是不可信輸入。

## Defense in depth / 多層防護

### 1. No destructive tools

There is no MCP tool for INSERT/UPDATE/DELETE, DDL, DAG trigger, DAG clear, secret update, or destructive platform operations.

### 2. SQLGlot AST policy

`ensure_read_only_sql()` parses SQL instead of relying only on keyword prefixes.

Rejected patterns include:

- DML: INSERT / UPDATE / DELETE / MERGE
- DDL: CREATE / ALTER / DROP / TRUNCATE
- privilege/transaction changes
- `SELECT ... INTO`
- multi-statement SQL
- write expressions hidden inside CTEs

`SHOW` and `EXPLAIN <read-only-query>` remain supported.

### 3. Database-side read-only mode

PostgreSQL:

```text
default_transaction_read_only=on
statement_timeout=<configured milliseconds>
```

Vertica:

```sql
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
```

The database account itself must still have least privilege. Application validation is not a replacement for database authorization.

### 4. MCP bearer authentication

When:

```bash
DPMCP_TRANSPORT=streamable-http
DPMCP_AUTH_ENABLED=true
```

the server configures MCP Python SDK v2 `TokenVerifier` + `AuthSettings`. Invalid/missing bearer tokens are rejected by the HTTP authorization layer before tool execution.

Authentication is HTTP-only. `stdio` is protected by the operating-system/process boundary rather than bearer headers.

### 5. RBAC

Roles are mapped to scopes:

| Role | Scopes |
|---|---|
| `reader` | `platform:read`, `catalog:read`, `runbook:read` |
| `analyst` | reader + `sql:explain`, `lineage:read` |
| `operator` | analyst + `operations:read`, `logs:read` |
| `admin` | all current read-only scopes + `audit:read` |

Every MCP tool calls `require_scope()` before the backend action.

### 6. Audit

Every tool/resource/prompt invocation records:

- UTC timestamp
- action name
- actor / subject
- role
- outcome
- latency
- bounded non-secret metadata
- exception type on failure

Raw bearer tokens are never audit fields. SQL statements are represented by a SHA-256-derived short fingerprint instead of raw SQL text.

### 7. Read-only integrations

- Airflow: GET-only `/api/v2` calls
- OpenSearch: search only
- Loki: `query_range` only
- PostgreSQL: catalog + EXPLAIN only
- Vertica: system catalog + EXPLAIN only

## Static token configuration

Static tokens are a portfolio/reference implementation for resource-server authorization. Do not commit token values.

```bash
export DPMCP_API_TOKENS_JSON='{
  "replace-me":{"client_id":"catalog-agent","role":"reader"}
}'
```

For v0.4 production delivery, replace static tokens with OIDC/JWT validation or RFC 7662 introspection against Keycloak, Entra ID, Auth0, or another authorization server.
