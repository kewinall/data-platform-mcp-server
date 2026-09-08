# Integrations / 整合設定

## Airflow 3

**繁體中文**：v0.2 使用 Airflow 3 穩定公開 REST API `/api/v2`，目前只做唯讀 DAG discovery 與最新 DAG Run 狀態查詢。

**English**: v0.2 uses Airflow 3's stable public REST API under `/api/v2`. The integration is read-only and currently covers DAG discovery and latest DAG-run state.

```bash
export DPMCP_OPERATIONS_MODE=airflow
export DPMCP_AIRFLOW_BASE_URL=https://airflow.example.internal
export DPMCP_AIRFLOW_TOKEN=replace-me
```

Required API access:
- `GET /api/v2/dags`
- `GET /api/v2/dags/{dag_id}/dagRuns`

Use an identity that can read only the DAG metadata required by this server.

## OpenSearch

```bash
export DPMCP_LOGS_MODE=opensearch
export DPMCP_OPENSEARCH_URL=https://opensearch.example.internal
export DPMCP_OPENSEARCH_INDEX='etl-logs-*'
export DPMCP_OPENSEARCH_USERNAME=readonly_user
export DPMCP_OPENSEARCH_PASSWORD=replace-me
```

The adapter sends `_search` only. Give the account index read/search permission, not write/admin privileges.

## Grafana Loki

```bash
export DPMCP_LOGS_MODE=loki
export DPMCP_LOKI_URL=https://loki.example.internal
export DPMCP_LOKI_TOKEN=replace-me
export DPMCP_LOKI_QUERY='{job=~".+"} |= "{query}"'
```

The adapter calls `GET /loki/api/v1/query_range` only. `{query}` is safely escaped before substitution.

## Adapter combinations

Catalog, orchestration, and log search are independently configurable. Example:

```bash
DPMCP_MODE=postgres
DPMCP_OPERATIONS_MODE=airflow
DPMCP_LOGS_MODE=loki
```

This allows a production deployment to use PostgreSQL catalog metadata, Airflow orchestration status, and Loki logs without changing MCP tool contracts.
