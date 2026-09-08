# Architecture / 架構

## Application layers

```text
MCP Host
  -> MCPServer v2
    -> Bearer authentication
       -> StaticTokenVerifier or OidcJwtVerifier
    -> RBAC scope check
    -> TenantPolicy
    -> AuditLogger + OpenTelemetry
    -> DataPlatformService
       -> CatalogAdapter
          -> Demo
          -> PostgreSQL
          -> Vertica
          -> Composite
       -> OperationsAdapter
          -> Demo / Airflow
       -> LogSearchAdapter
          -> Demo / OpenSearch / Loki
       -> RunbookAdapter
```

The MCP protocol surface does not know how a database is implemented. Backend-specific behavior is isolated in adapters.

## Authorization model

```text
JWT / static token
      |
      v
 Principal
      |
      +--> role -> scopes -> operation permission
      |
      +--> tenant -> allowed sources -> catalog boundary
```

Example:

```text
role=analyst
tenant=tenant-a
tenant-a sources=[postgres]

get_table_metadata(postgres, ...) -> allowed
explain_sql(postgres, ...)       -> allowed
get_table_metadata(vertica, ...) -> denied
list_dags()                      -> denied (analyst lacks operations:read)
```

## Lineage model

Two forms remain separate:

1. catalog-backed lineage from database metadata;
2. SQL-derived lineage from SQLGlot AST parsing.

This prevents inferred SQL relationships from being presented as catalog-observed facts.

## OpenTelemetry

Every MCP invocation is wrapped in an application span. Low-cardinality invocation metrics are also emitted. A trace ID is copied into the audit record for correlation.

Sensitive values such as bearer tokens, raw SQL, DSNs, and passwords are not telemetry attributes.

## Kubernetes

```text
Namespace (Pod Security Restricted)
       |
Deployment -> Service -> MCP clients
       |
       +-> ConfigMap
       +-> Secret / ExternalSecret
       +-> NetworkPolicy
       +-> PDB
       +-> optional HPA
       |
       +-> PostgreSQL / Vertica
       +-> IdP/JWKS
       +-> Airflow / logs
       +-> OTLP Collector
```

The application ServiceAccount token is disabled because the server itself does not require Kubernetes API access.
