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

### Streamable HTTP

```bash
DPMCP_TRANSPORT=streamable-http DPMCP_PORT=8000 data-platform-mcp
```

Client endpoint: `http://localhost:8000/mcp`

## Docker

```bash
cp .env.example .env
docker compose up --build
```

## PostgreSQL

Create a dedicated read-only account and grant only the schemas/tables the MCP server should inspect. Do not reuse an administrator or application owner account.

```bash
DPMCP_MODE=postgres \
DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@localhost:5432/analytics' \
data-platform-mcp
```
