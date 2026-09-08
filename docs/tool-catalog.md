# MCP Tool Catalog / MCP 工具目錄

| Tool | Inputs | Output | Risk |
|---|---|---|---|
| `health` | none | status/version | Read-only |
| `list_data_sources` | none | source names | Read-only |
| `list_schemas` | source | schema names | Read-only |
| `list_tables` | source, schema | table/view names | Read-only |
| `describe_table` | source, schema, table | column metadata | Read-only |
| `table_statistics` | source, schema, table | estimated row count/notes | Read-only |
| `explain_sql` | source, sql | explain plan | Guarded read-only SQL |
| `list_dags` | none | DAG metadata | Read-only |
| `get_dag_status` | dag_id | latest state | Read-only |
| `search_etl_logs` | query, limit | log hits | Read-only |
| `search_runbooks` | query, limit | knowledge hits | Read-only |

## 設計原則 / Design principles

- No destructive tool exists in v0.1.
- Tool outputs are structured and bounded.
- Demo mode is deterministic and synthetic.
- Production adapters must enforce least privilege independently from MCP-level validation.
