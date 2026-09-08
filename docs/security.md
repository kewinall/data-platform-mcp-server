# Security Design / 安全設計

## Threat model / 威脅模型

The MCP server can become an automation bridge between an LLM host and enterprise systems. Therefore a prompt mistake must not automatically become a write operation.

## v0.1 controls

- No destructive MCP tools.
- SQL allow-list behavior: `SELECT`, `WITH`, `EXPLAIN`, `SHOW` only.
- Explicit rejection of write/DDL keywords and multi-statement SQL.
- PostgreSQL connections enable `default_transaction_read_only=on`.
- PostgreSQL statement timeout.
- Recommended database-side read-only account.
- Synthetic demo data by default.
- Secrets are environment variables and `.env` is gitignored.
- CI dependency and filesystem vulnerability scanning.

## Limitations

Keyword validation is defense-in-depth, not a SQL parser and not an authorization boundary. Production deployments must rely on backend least privilege, network policy, identity, auditing, and allow-listed integrations.
