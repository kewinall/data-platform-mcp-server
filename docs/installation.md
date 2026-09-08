# Installation / 安裝

## Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

### stdio

```bash
DPMCP_TRANSPORT=stdio data-platform-mcp
```

`stdio` is intended for a locally launched MCP Host. HTTP bearer authentication does not apply to stdio.

### Streamable HTTP

```bash
DPMCP_TRANSPORT=streamable-http DPMCP_PORT=8000 data-platform-mcp
```

Client endpoint:

```text
http://localhost:8000/mcp
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The image runs as non-root user `appuser` (UID 10001).

## PostgreSQL

Create a dedicated read-only account and grant only the schemas/tables the MCP server should inspect.

```bash
DPMCP_MODE=postgres \
DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@localhost:5432/analytics' \
data-platform-mcp
```

## Vertica

Use a dedicated read-only user and TLS appropriate for your environment.

```bash
DPMCP_MODE=vertica \
DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@localhost:5433/warehouse?tlsmode=require' \
data-platform-mcp
```

The adapter also sets the Vertica session to transaction `READ ONLY` before catalog/EXPLAIN work.

## PostgreSQL + Vertica

```bash
DPMCP_MODE=multi \
DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@postgres:5432/analytics' \
DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@vertica:5433/warehouse' \
data-platform-mcp
```

## Streamable HTTP authentication

```bash
export DPMCP_TRANSPORT=streamable-http
export DPMCP_AUTH_ENABLED=true
export DPMCP_AUTH_ISSUER_URL='https://auth.example.com'
export DPMCP_AUTH_RESOURCE_URL='http://127.0.0.1:8000/mcp'
export DPMCP_API_TOKENS_JSON='{"replace-me":{"client_id":"catalog-agent","role":"reader"}}'
data-platform-mcp
```

Never commit real token values. Static bearer tokens are the v0.3 reference implementation; v0.4 plans OIDC/JWT integration.

## Audit JSONL

```bash
export DPMCP_AUDIT_ENABLED=true
export DPMCP_AUDIT_LOG_PATH=/var/log/data-platform-mcp/audit.jsonl
```

Ensure the runtime user has write permission to the parent directory when file output is enabled.
