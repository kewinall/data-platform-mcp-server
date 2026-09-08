# Security Design / 安全設計

## Threat model

The MCP server bridges LLM clients and enterprise data systems. Prompt injection, a compromised MCP client, stolen application credentials, or an overly broad network path must not automatically become a data-platform write path.

## 1. No destructive MCP tools

There is no tool for database mutation, DDL, privilege changes, DAG trigger/clear, log deletion, or secret modification.

## 2. SQL policy

SQLGlot parses a single statement and rejects write/DDL expressions, `SELECT INTO`, write CTEs, and multi-statements.

Database-side controls remain enabled:

- PostgreSQL: `default_transaction_read_only=on`
- Vertica: `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`

## 3. Authentication

Streamable HTTP can use either:

```text
static token -> demo/reference
OIDC JWT     -> production-oriented resource-server mode
```

OIDC validation checks:

- JWKS signature
- algorithm allow-list
- issuer
- audience
- expiration
- subject

The MCP SDK remains responsible for the HTTP bearer gate and protected resource metadata behavior.

## 4. RBAC

| Role | Capabilities |
|---|---|
| reader | platform/catalog/runbook |
| analyst | reader + SQL explain + lineage |
| operator | analyst + operations/logs |
| admin | all current read-only scopes + audit |

Unknown OIDC roles are rejected.

## 5. Tenant-aware source isolation

`DPMCP_TENANT_ALLOWED_SOURCES_JSON` maps a tenant identity to allowed catalog source names.

```json
{
  "tenant-a": ["postgres"],
  "tenant-b": ["vertica"]
}
```

The policy is checked before schema/table/metadata/lineage/EXPLAIN calls.

This is **source-level isolation**, not row-level security. Production databases should still enforce schema/table/row policies appropriate to the organization.

## 6. Audit

Audit contains:

- timestamp
- actor
- subject
- tenant
- role
- action
- outcome
- latency
- error type
- safe metadata
- trace ID when available

Bearer tokens are never audit fields. SQL uses a fingerprint instead of the raw statement.

## 7. OpenTelemetry

Telemetry exports action/role/tenant/outcome and latency. Raw SQL, DSNs, passwords, and tokens are excluded.

## 8. Kubernetes hardening

The Helm chart defaults include:

- non-root user
- read-only root filesystem
- `allowPrivilegeEscalation: false`
- `capabilities.drop: [ALL]`
- `seccompProfile: RuntimeDefault`
- ServiceAccount token automount disabled
- CPU/memory requests and limits
- NetworkPolicy
- PodDisruptionBudget

The included namespace example applies Kubernetes Pod Security `restricted`.

## 9. NetworkPolicy

Default application egress is DNS only. Production values must explicitly allow required destinations.

Do not set `networkPolicy.egress.allowAll=true` merely to bypass configuration unless the surrounding network architecture supplies equivalent controls.

## 10. Secrets

Use environment variables from a Kubernetes Secret or External Secrets Operator. Do not commit credentials into values files.

The included Azure example uses Key Vault + Workload Identity through External Secrets Operator.

## 11. Defense in depth

Application validation is not an authorization boundary by itself. Production environments must additionally use:

- database least privilege
- TLS
- network segmentation
- identity-provider policy
- secret rotation
- Kubernetes admission controls
- centralized audit/monitoring
- vulnerability management
