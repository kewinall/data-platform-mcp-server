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
       -> ETLMetadataContractAdapter
          -> Synthetic demo contract
          -> Read-only exported JSON directory
```

The MCP protocol surface does not know how a database is implemented. Backend-specific behavior is isolated in adapters.

Normalized ETL metadata is also adapter-backed, but its authority is different: enterprise-etl-platform produces the ETL truth and this server only exposes that existing contract. It does not reparse Pentaho/Hop or create missing lineage.

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

Three sources remain explicit:

1. catalog-backed lineage from database metadata;
2. SQL-derived lineage from SQLGlot AST parsing;
3. ETL producer lineage from enterprise-etl-platform normalized metadata.

ETL producer lineage preserves structural, inferred-deterministic, and AI interpretation classifications. The MCP layer does not promote or merge these classifications into a stronger claim. This prevents inferred or AI relationships from being presented as deterministic facts.

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
       +-> read-only ETL metadata PVC
```

The application ServiceAccount token is disabled because the server itself does not require Kubernetes API access.
