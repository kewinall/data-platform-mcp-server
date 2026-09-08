# MCP Tool Catalog / MCP 工具目錄

| Tool | Inputs | Required scope | Output / Purpose |
|---|---|---|---|
| `health` | none | `platform:read` | status/version |
| `whoami` | none | `platform:read` | actor, role, scopes |
| `list_data_sources` | none | `catalog:read` | source names |
| `list_schemas` | source | `catalog:read` | schema names |
| `list_tables` | source, schema | `catalog:read` | table/view names |
| `describe_table` | source, schema, table | `catalog:read` | column metadata |
| `table_statistics` | source, schema, table | `catalog:read` | lightweight row statistics |
| `get_table_metadata` | source, schema, table | `catalog:read` | owner/type/projections/attributes |
| `get_table_lineage` | source, schema, table | `lineage:read` | catalog-backed lineage edges |
| `analyze_sql_lineage` | sql | `lineage:read` | SQL input tables and CTEs |
| `explain_sql` | source, sql | `sql:explain` | guarded database EXPLAIN |
| `list_dags` | none | `operations:read` | DAG metadata |
| `get_dag_status` | dag_id | `operations:read` | latest DAG state |
| `search_etl_logs` | query, limit | `logs:read` | log hits |
| `search_runbooks` | query, limit | `runbook:read` | knowledge hits |

## Resources

| Resource | Scope | Description |
|---|---|---|
| `platform://capabilities` | `platform:read` | active adapters/auth/audit/safety |
| `catalog://{source}/{schema}/{table}` | `catalog:read` | governed table metadata |

## Prompts

| Prompt | Scope | Purpose |
|---|---|---|
| `incident_triage` | `operations:read` | DAG/log/runbook incident investigation |
| `data_discovery` | `catalog:read` | metadata + lineage first data discovery |
