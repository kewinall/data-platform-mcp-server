# MCP Tool Catalog / MCP 工具目錄

| Tool | Required scope | Tenant source check | Purpose |
|---|---|---:|---|
| `health` | `platform:read` | — | status/version |
| `whoami` | `platform:read` | — | actor, role, tenant, scopes |
| `list_data_sources` | `catalog:read` | filter | tenant-visible sources |
| `list_schemas` | `catalog:read` | yes | schema names |
| `list_tables` | `catalog:read` | yes | table/view names |
| `describe_table` | `catalog:read` | yes | columns |
| `table_statistics` | `catalog:read` | yes | lightweight statistics |
| `get_table_metadata` | `catalog:read` | yes | owner/type/projections |
| `get_table_lineage` | `lineage:read` | yes | catalog lineage |
| `analyze_sql_lineage` | `lineage:read` | — | parse caller-provided SQL |
| `explain_sql` | `sql:explain` | yes | guarded DB EXPLAIN |
| `list_dags` | `operations:read` | — | DAG metadata |
| `get_dag_status` | `operations:read` | — | latest DAG state |
| `search_etl_logs` | `logs:read` | — | log search |
| `search_runbooks` | `runbook:read` | — | runbook search |
| `list_etl_pipelines` | `catalog:read` | — | producer-published ETL pipelines |
| `get_etl_pipeline` | `catalog:read` | — | normalized ETL metadata contract |
| `get_etl_pipeline_steps` | `catalog:read` | — | deterministic ETL step metadata |
| `get_etl_pipeline_dependencies` | `lineage:read` | — | step/workflow dependency records |
| `get_etl_table_lineage` | `lineage:read` | — | producer lineage + capability boundary |
| `search_etl_metadata` | `catalog:read` | — | ETL metadata discovery |

v0.5 preserves v0.4 tenant isolation for catalog/data-source operations. ETL metadata artifacts are deployment-scoped; shared multi-tenant ETL metadata requires an explicit artifact policy or separated MCP deployments. Deployments requiring tenant-specific Airflow/log/runbook segregation should use tenant-separated backends or extend the policy layer for those resources.
