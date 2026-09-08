# Architecture / 架構

## 核心設計 / Core design

`data-platform-mcp-server` 將 MCP-facing capability、authorization/audit policy 與 backend integration 分離。MCP Tool 不直接連接 PostgreSQL、Vertica、Airflow 或 log backend，而是透過 `DataPlatformService` 與 Adapter Protocol。

The project separates MCP-facing capabilities, authorization/audit policy, and backend-specific integrations. Tools call `DataPlatformService`; adapters encapsulate external systems.

```text
MCP Host
  -> MCPServer v2
    -> Bearer Auth (HTTP only)
      -> RBAC scope check
        -> Audit wrapper
          -> DataPlatformService
            -> CatalogAdapter
              -> Demo
              -> PostgreSQL
              -> Vertica
              -> Composite(PostgreSQL + Vertica)
            -> OperationsAdapter
              -> Demo / Airflow 3
            -> LogSearchAdapter
              -> Demo / OpenSearch / Loki
            -> RunbookAdapter
```

## Metadata and lineage

Two complementary lineage paths are provided:

1. **Catalog-backed lineage** — backend metadata such as Vertica `v_catalog.view_tables`.
2. **SQL-derived lineage** — SQLGlot AST extraction of referenced input tables and CTEs.

This separation makes it clear whether lineage is an observed catalog relationship or an inferred relationship from SQL text.

## Catalog routing

`DPMCP_MODE=multi` constructs a `CompositeCatalogAdapter`. Each backend advertises a unique source name, and the composite routes the call without exposing backend-specific behavior to MCP tools.

```text
list_data_sources()
  -> ["postgres", "vertica"]

get_table_metadata("vertica", "mart", "daily_sales")
  -> VerticaCatalogAdapter

get_table_metadata("postgres", "public", "orders")
  -> PostgresCatalogAdapter
```

## Security path

```text
HTTP request
 -> MCP SDK BearerAuthBackend
 -> required platform:read scope
 -> per-tool RBAC scope
 -> audit start
 -> read-only service action
 -> audit outcome + latency
```

Database-side read-only mode remains enabled even after application-layer SQL validation.
