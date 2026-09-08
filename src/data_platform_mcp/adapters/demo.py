from data_platform_mcp.models import ColumnInfo, DagInfo, SearchHit, TableInfo, TableStatistics
from data_platform_mcp.security import ensure_read_only_sql


class DemoCatalogAdapter:
    """Synthetic catalog used for CI, demos, and screenshots."""

    _tables = {
        "analytics": {
            "public": {
                "customers": [
                    ColumnInfo(name="customer_id", data_type="bigint", nullable=False),
                    ColumnInfo(name="segment", data_type="varchar", nullable=True),
                    ColumnInfo(name="created_at", data_type="timestamp", nullable=False),
                ],
                "orders": [
                    ColumnInfo(name="order_id", data_type="bigint", nullable=False),
                    ColumnInfo(name="customer_id", data_type="bigint", nullable=False),
                    ColumnInfo(name="amount", data_type="numeric(12,2)", nullable=False),
                    ColumnInfo(name="ordered_at", data_type="timestamp", nullable=False),
                ],
            },
            "mart": {
                "daily_sales": [
                    ColumnInfo(name="business_date", data_type="date", nullable=False),
                    ColumnInfo(name="revenue", data_type="numeric(14,2)", nullable=False),
                ]
            },
        }
    }

    def list_sources(self) -> list[str]:
        return sorted(self._tables)

    def list_schemas(self, source: str) -> list[str]:
        return sorted(self._tables.get(source, {}))

    def list_tables(self, source: str, schema: str) -> list[str]:
        return sorted(self._tables.get(source, {}).get(schema, {}))

    def describe_table(self, source: str, schema: str, table: str) -> TableInfo:
        try:
            columns = self._tables[source][schema][table]
        except KeyError as exc:
            raise ValueError(f"Unknown table: {source}.{schema}.{table}") from exc
        return TableInfo(schema_name=schema, table_name=table, columns=columns)

    def table_statistics(self, source: str, schema: str, table: str) -> TableStatistics:
        self.describe_table(source, schema, table)
        counts = {"customers": 125000, "orders": 2400000, "daily_sales": 730}
        return TableStatistics(
            schema_name=schema,
            table_name=table,
            row_count=counts.get(table),
            notes=["Synthetic demo statistics; no production data is queried."],
        )

    def explain_sql(self, source: str, sql: str) -> str:
        if source not in self._tables:
            raise ValueError(f"Unknown source: {source}")
        safe_sql = ensure_read_only_sql(sql)
        return (
            "DEMO PLAN\n"
            "  -> Seq Scan / synthetic planner\n"
            f"  -> Statement: {safe_sql}\n"
            "No database was contacted."
        )


class DemoOperationsAdapter:
    _dags = {
        "customer_daily_sync": DagInfo(
            dag_id="customer_daily_sync", state="success", last_run="2026-09-08T01:00:00Z"
        ),
        "sales_mart_refresh": DagInfo(
            dag_id="sales_mart_refresh", state="running", last_run="2026-09-08T14:00:00Z"
        ),
        "quality_checks": DagInfo(
            dag_id="quality_checks", state="failed", last_run="2026-09-08T14:15:00Z"
        ),
    }

    def list_dags(self) -> list[DagInfo]:
        return sorted(self._dags.values(), key=lambda item: item.dag_id)

    def get_dag_status(self, dag_id: str) -> DagInfo:
        try:
            return self._dags[dag_id]
        except KeyError as exc:
            raise ValueError(f"Unknown DAG: {dag_id}") from exc


class DemoLogAdapter:
    _logs = [
        SearchHit(
            source="airflow",
            title="quality_checks / task validate_orders",
            snippet="Row-count guardrail failed: expected >= 10000, observed 9321.",
            metadata={"level": "ERROR", "environment": "demo"},
        ),
        SearchHit(
            source="hop",
            title="sales_mart_refresh",
            snippet="Pipeline completed with 2400000 input rows and 730 aggregate rows.",
            metadata={"level": "INFO", "environment": "demo"},
        ),
    ]

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        needle = query.lower().strip()
        matches = [
            hit
            for hit in self._logs
            if needle in hit.title.lower() or needle in hit.snippet.lower()
        ]
        return matches[:limit]


class DemoRunbookAdapter:
    _docs = [
        SearchHit(
            source="runbook",
            title="Airflow DAG failure triage",
            snippet=(
                "Check failed task logs, upstream dependencies, retries, pools, and recent "
                "deploys."
            ),
            metadata={"path": "runbooks/airflow-dag-failure.md"},
        ),
        SearchHit(
            source="runbook",
            title="Database latency triage",
            snippet=(
                "Review active sessions, lock waits, query plan regression, and resource "
                "saturation."
            ),
            metadata={"path": "runbooks/database-latency.md"},
        ),
    ]

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        needle = query.lower().strip()
        return [
            hit
            for hit in self._docs
            if needle in hit.title.lower() or needle in hit.snippet.lower()
        ][:limit]
