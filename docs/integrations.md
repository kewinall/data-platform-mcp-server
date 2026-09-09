# Integrations / 整合說明

## PostgreSQL

```bash
export DPMCP_MODE=postgres
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@postgres:5432/analytics'
```

The adapter reads `information_schema`, uses `pg_class.reltuples` for lightweight estimates, and runs `EXPLAIN (FORMAT TEXT)` only after SQL policy validation. Connections set `default_transaction_read_only=on`.

## Vertica

v0.3 uses the official `vertica-python` DB-API client.

```bash
export DPMCP_MODE=vertica
export DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@vertica:5433/warehouse?tlsmode=require'
export DPMCP_VERTICA_SOURCE_NAME=vertica
```

Every connection executes:

```sql
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
```

Catalog sources:

- `v_catalog.schemata`
- `v_catalog.all_tables`
- `v_catalog.columns`
- `v_catalog.view_columns`
- `v_catalog.projections`
- `v_catalog.view_tables`
- `v_monitor.projection_storage`

The adapter does not run `COUNT(*)` for table statistics. It derives a lightweight row count from projection storage.

### Multi-source mode

```bash
export DPMCP_MODE=multi
export DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@postgres:5432/analytics'
export DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@vertica:5433/warehouse'
```

Either DSN may be omitted in `multi` mode as long as at least one catalog backend is configured.

## Airflow 3

```bash
export DPMCP_OPERATIONS_MODE=airflow
export DPMCP_AIRFLOW_BASE_URL='https://airflow.example.internal'
export DPMCP_AIRFLOW_TOKEN='replace-me'
```

The adapter uses the stable public `/api/v2` API and GET operations only.

## OpenSearch

```bash
export DPMCP_LOGS_MODE=opensearch
export DPMCP_OPENSEARCH_URL='https://opensearch.example.internal'
export DPMCP_OPENSEARCH_INDEX='etl-logs-*'
```

Only `_search` is used.

## Grafana Loki

```bash
export DPMCP_LOGS_MODE=loki
export DPMCP_LOKI_URL='https://loki.example.internal'
export DPMCP_LOKI_QUERY='{job=~".+"} |= "{query}"'
```

Only `query_range` is used.


## ETL Metadata Producer

enterprise-etl-platform owns parsing, normalized metadata, migration analysis, and lineage truth.
This MCP server consumes exported JSON only.

~~~bash
export DPMCP_ETL_METADATA_DIR=/srv/etl-metadata
export DPMCP_ETL_METADATA_MAX_FILES=500
~~~

The server does not parse Pentaho KTR/KJB or Apache Hop artifacts. In Kubernetes, the Helm
chart can mount an existing PVC read-only through etlMetadata.enabled / existingClaim.

See docs/etl-metadata-integration.md for tool contracts, lineage semantics, failure behavior,
and the multi-tenant capability boundary.
