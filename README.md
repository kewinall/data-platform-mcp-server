# Data Platform MCP Server

**目前版本 / Current release: v0.4.0**

> **📘 Interactive Project Guide / 專案互動式說明文件**  
> [Open the single-file HTML guide](docs/data-platform-mcp-server-guide.html) — 面試官速讀、架構圖、MCP Tools、Security、OIDC/RBAC/Multi-tenancy、Kubernetes/Helm、CI/CD 與使用教學集中在同一頁。

> **繁體中文**：企業資料平台的 **Tool / Integration Layer**。這是一個 production-oriented Model Context Protocol (MCP) Server，將 PostgreSQL、Vertica、Airflow、Logs、Metadata 與 Lineage 以安全、標準化的 Tool Contract 提供給 AI Agent / IDE / MCP Host。
>
> **English**: The **Tool / Integration Layer** for an enterprise data platform. This production-oriented MCP server exposes PostgreSQL, Vertica, Airflow, logs, metadata, and lineage through standardized, governed tool contracts for AI agents, IDEs, and MCP hosts.

Repository 預設使用 synthetic demo data，不含任何公司/客戶資料、真實帳密或內部 URL。

## Portfolio Role / 作品集角色

**Primary role: Tool & Integration Platform / AI 工具與資料平台整合層**

此 Repository 主要回答：**如何讓不同 AI Agent 透過標準化 MCP Protocol，安全地存取企業 Data Platform 的 Metadata、Lineage、Airflow、Logs 與 Read-only SQL 能力？**  
This repository primarily answers: **How can heterogeneous AI clients safely access enterprise data-platform capabilities through standardized MCP tools?**

Portfolio responsibility boundary:

- **This repository:** canonical MCP server, tool contracts, protocol transport, catalog/data-platform adapters, tool-level auth/scope/tenant controls.
- [Agentic DataOps Copilot](https://github.com/kewinall/agentic-dataops-copilot): reasoning and operations client that can consume this tool layer.
- [Enterprise RAG Platform](https://github.com/kewinall/enterprise-rag-platform): knowledge ingestion, retrieval, grounding, citations, and evaluation.
- [Multi-LLM AI Gateway](https://github.com/kewinall/multi-llm-ai-gateway): centralized model control plane.

**Intentional scope boundary:** this server does **not** implement autonomous agent orchestration, RAG chat, or model routing. Those responsibilities belong to the other portfolio layers.

## Reference Integration / 參考整合

    Agentic DataOps Copilot
              |
              | MCP
              v
    Data Platform MCP Server
              |
      +-------+--------+---------+----------+
      |       |        |         |          |
 PostgreSQL Vertica Airflow   Logs     Metadata/Lineage

Other MCP hosts such as ChatGPT, Claude, Codex, or IDE agents can connect to the same server-side tool contract.

## v0.4 Highlights

### Data Platform
- PostgreSQL + Vertica catalog adapters
- multi-source composite catalog
- metadata / projection metadata
- catalog-backed lineage
- SQLGlot AST SQL lineage
- read-only SQL policy
- Airflow 3 `/api/v2`
- OpenSearch / Loki log search

### Identity / Security
- MCP Python SDK v2
- Streamable HTTP bearer authentication
- static token reference mode
- OIDC/JWT + JWKS verification
- Keycloak / Microsoft Entra ID examples
- roles: `reader`, `analyst`, `operator`, `admin`
- per-tool scopes
- tenant-aware catalog source isolation
- structured audit JSONL
- SQL fingerprints instead of raw SQL audit text

### Production Delivery
- Kubernetes Helm chart
- Restricted-style Pod Security defaults
- NetworkPolicy
- PodDisruptionBudget
- optional HPA
- External Secrets Operator v1
- Azure Key Vault Workload Identity example
- OpenTelemetry traces + metrics over OTLP/HTTP
- air-gapped bundle builder
- CI/Security-gated automatic Git tag + GitHub Release
- packaged Helm chart attached to releases

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
       |
 Composite multi-source routing
       |
 Metadata / Lineage / SQL Policy
```

Kubernetes deployment:

```text
External Client / MCP Host
          |
          v
   Kubernetes Service
          |
   NetworkPolicy
          |
  MCP Server Pods (2+)
    |     |       |
    |     |       +--> OTLP Collector
    |     +----------> OIDC / JWKS
    +----------------> DB / Airflow / Logs

External Secrets Operator
          |
   Vault / Key Vault
          |
   Kubernetes Secret
          |
       MCP Pods
```

## MCP Tools

| Tool | Scope | Purpose |
|---|---|---|
| `health` | `platform:read` | health/version |
| `whoami` | `platform:read` | identity, role, tenant, scopes |
| `list_data_sources` | `catalog:read` | tenant-visible sources |
| `list_schemas` | `catalog:read` | schemas |
| `list_tables` | `catalog:read` | tables/views |
| `describe_table` | `catalog:read` | column metadata |
| `table_statistics` | `catalog:read` | lightweight statistics |
| `get_table_metadata` | `catalog:read` | owner/type/projections |
| `get_table_lineage` | `lineage:read` | catalog lineage |
| `analyze_sql_lineage` | `lineage:read` | SQL AST lineage |
| `explain_sql` | `sql:explain` | guarded EXPLAIN |
| `list_dags` | `operations:read` | DAG discovery |
| `get_dag_status` | `operations:read` | latest DAG state |
| `search_etl_logs` | `logs:read` | ETL log search |
| `search_runbooks` | `runbook:read` | troubleshooting knowledge |

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

Endpoint:

```text
http://127.0.0.1:8000/mcp
```

## Multi-source PostgreSQL + Vertica

```bash
export DPMCP_MODE=multi
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@postgres:5432/analytics'
export DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@vertica:5433/warehouse?tlsmode=require'
data-platform-mcp
```

## OIDC + Tenant-aware RBAC

```bash
export DPMCP_TRANSPORT=streamable-http
export DPMCP_AUTH_ENABLED=true
export DPMCP_AUTH_MODE=oidc
export DPMCP_AUTH_ISSUER_URL='https://idp.example.com/realms/data-platform'
export DPMCP_AUTH_RESOURCE_URL='https://mcp.example.com/mcp'
export DPMCP_OIDC_JWKS_URL='https://idp.example.com/realms/data-platform/protocol/openid-connect/certs'
export DPMCP_OIDC_AUDIENCE='data-platform-mcp'
export DPMCP_OIDC_ROLE_CLAIM='realm_access.roles'
export DPMCP_OIDC_TENANT_CLAIM='tenant'
export DPMCP_OIDC_ROLE_MAP_JSON='{"data-platform-analyst":"analyst"}'

export DPMCP_TENANT_ENABLED=true
export DPMCP_TENANT_ALLOWED_SOURCES_JSON='{"tenant-a":["postgres"],"tenant-b":["vertica"]}'

data-platform-mcp
```

Role answers **what** the caller may do; tenant policy answers **which catalog source** the caller may access.

See `docs/oidc.md`.

## OpenTelemetry

```bash
export DPMCP_OTEL_ENABLED=true
export DPMCP_OTEL_EXPORTER_OTLP_ENDPOINT='http://otel-collector:4318'
export DPMCP_DEPLOYMENT_ENVIRONMENT=prod
```

Signals:

```text
Traces:
  dpmcp.<action>

Metrics:
  dpmcp.invocations
  dpmcp.invocation.duration
```

Audit events include the OpenTelemetry trace ID when available.

See `docs/observability.md`.

## Kubernetes / Helm

```bash
kubectl apply -f examples/kubernetes/namespace-restricted.yaml

helm upgrade --install dpmcp   deploy/helm/data-platform-mcp-server   --namespace data-platform-mcp
```

Default chart security posture:

```text
runAsNonRoot                true
runAsUser                   10001
readOnlyRootFilesystem      true
allowPrivilegeEscalation    false
capabilities                drop ALL
seccompProfile              RuntimeDefault
ServiceAccount token        disabled
NetworkPolicy               enabled
non-DNS egress              denied by default
```

See `docs/deployment.md`.

## External Secrets

The Helm chart can consume either an existing Kubernetes Secret or create one through External Secrets Operator.

Azure Key Vault Workload Identity example:

```text
examples/external-secrets/azure-key-vault-secretstore.yaml
```

## Air-gapped Bundle

On an internet-connected staging machine:

```bash
make airgap
```

Output:

```text
dist/data-platform-mcp-server-0.4.0-airgap.tar.gz
```

It contains a Python wheelhouse, container image tar, Helm package, documentation, and SHA256 checksums.

See `docs/airgap.md`.

## CI / Security / Release

```text
CI
├── Python 3.11
├── Python 3.12
├── Ruff
├── pytest
├── compileall
├── Docker build
├── shell syntax
├── Helm lint
└── Helm template

Security
├── pip-audit
├── Trivy filesystem
└── Trivy rendered Kubernetes config

Both green
   ↓
Git Tag
   ↓
GitHub Release
   ↓
Helm chart .tgz asset
```

## Security Boundaries

1. No destructive MCP tool exists.
2. SQLGlot AST policy rejects write/DDL/multi-statement SQL.
3. PostgreSQL and Vertica also use database/session read-only controls.
4. OIDC JWT verification validates signature/issuer/audience/expiry/subject.
5. Unknown roles are rejected.
6. Tenant isolation is source-level in v0.4; it is not row-level RLS.
7. Tokens, passwords, DSNs, and raw SQL are excluded from normal audit/telemetry metadata.
8. Kubernetes egress is deny-by-default except DNS in the Helm defaults.
9. Backend least privilege remains mandatory.

## Roadmap

- **v0.1** ✅ MCP foundation + PostgreSQL
- **v0.2** ✅ Airflow 3 + OpenSearch/Loki + MCP resources/prompts
- **v0.3** ✅ Vertica + metadata/lineage + AST SQL policy + RBAC/audit
- **v0.4** ✅ Kubernetes/Helm + OIDC + multi-tenancy + OTel + External Secrets + air-gap

Potential next work should remain focused on the **tool/integration layer**, such as OPA/Cedar policy, OpenMetadata/DataHub, signed images/SBOM provenance, Gateway API, GitOps, protocol conformance, and additional read-only platform adapters. Agent orchestration and model routing are intentionally out of scope.

## Documentation

- `docs/architecture.md`
- `docs/installation.md`
- `docs/integrations.md`
- `docs/security.md`
- `docs/tool-catalog.md`
- `docs/deployment.md`
- `docs/oidc.md`
- `docs/observability.md`
- `docs/airgap.md`
- `docs/v0.4.md`
- `CHANGELOG.md`

## License

MIT License. See `LICENSE`.
