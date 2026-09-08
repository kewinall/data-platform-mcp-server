from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import vertica_python

from data_platform_mcp.models import (
    ColumnInfo,
    LineageEdge,
    LineageResult,
    TableInfo,
    TableMetadata,
    TableStatistics,
)
from data_platform_mcp.security import ensure_read_only_sql


class VerticaCatalogAdapter:
    """Read-only Vertica catalog adapter using the official vertica-python client."""

    def __init__(
        self,
        dsn: str,
        *,
        source_name: str = "vertica",
        connection_timeout: float = 10.0,
        session_label: str = "data-platform-mcp",
        connect_fn: Callable[..., Any] | None = None,
    ):
        self.dsn = dsn
        self.source_name = source_name
        self.connection_timeout = connection_timeout
        self.session_label = session_label
        self._connect_fn = connect_fn or vertica_python.connect

    @contextmanager
    def _cursor(self) -> Iterator[Any]:
        conn = self._connect_fn(
            dsn=self.dsn,
            autocommit=False,
            connection_timeout=self.connection_timeout,
            session_label=self.session_label,
        )
        cur = conn.cursor()
        try:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
            yield cur
        finally:
            try:
                conn.rollback()
            finally:
                cur.close()
                conn.close()

    def list_sources(self) -> list[str]:
        return [self.source_name]

    def _require_source(self, source: str) -> None:
        if source != self.source_name:
            raise ValueError(f"Vertica adapter exposes source name '{self.source_name}'")

    def list_schemas(self, source: str) -> list[str]:
        self._require_source(source)
        sql = """
            SELECT schema_name
            FROM v_catalog.schemata
            WHERE is_system_schema = false
            ORDER BY schema_name
        """
        with self._cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in cur.fetchall()]

    def list_tables(self, source: str, schema: str) -> list[str]:
        self._require_source(source)
        sql = """
            SELECT table_name
            FROM v_catalog.all_tables
            WHERE schema_name = %s
              AND table_type IN ('TABLE', 'VIEW', 'GLOBAL TEMPORARY', 'LOCAL TEMPORARY')
            ORDER BY table_name
        """
        with self._cursor() as cur:
            cur.execute(sql, (schema,))
            return [row[0] for row in cur.fetchall()]

    def describe_table(self, source: str, schema: str, table: str) -> TableInfo:
        self._require_source(source)
        sql = """
            SELECT column_name, data_type, is_nullable, ordinal_position
            FROM v_catalog.columns
            WHERE table_schema = %s AND table_name = %s
            UNION ALL
            SELECT column_name, data_type, true AS is_nullable, ordinal_position
            FROM v_catalog.view_columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY 4
        """
        with self._cursor() as cur:
            cur.execute(sql, (schema, table, schema, table))
            rows = cur.fetchall()
        if not rows:
            raise ValueError(f"Unknown table or view: {schema}.{table}")
        return TableInfo(
            schema_name=schema,
            table_name=table,
            columns=[
                ColumnInfo(name=name, data_type=data_type, nullable=bool(nullable))
                for name, data_type, nullable, _ in rows
            ],
        )

    def table_statistics(self, source: str, schema: str, table: str) -> TableStatistics:
        self._require_source(source)
        self.describe_table(source, schema, table)
        sql = """
            SELECT MAX(
                CASE WHEN p.is_segmented THEN s.sum_rows ELSE s.max_node_rows END
            ) AS estimated_rows
            FROM (
                SELECT projection_id, SUM(row_count) AS sum_rows, MAX(row_count) AS max_node_rows
                FROM v_monitor.projection_storage
                WHERE anchor_table_schema = %s AND anchor_table_name = %s
                GROUP BY projection_id
            ) s
            JOIN v_catalog.projections p ON p.projection_id = s.projection_id
        """
        with self._cursor() as cur:
            cur.execute(sql, (schema, table))
            row = cur.fetchone()
        return TableStatistics(
            schema_name=schema,
            table_name=table,
            row_count=int(row[0]) if row and row[0] is not None else None,
            notes=[
                "row_count is derived from Vertica projection storage; it avoids COUNT(*) and is "
                "intended for lightweight operational inspection."
            ],
        )

    def get_table_metadata(self, source: str, schema: str, table: str) -> TableMetadata:
        self._require_source(source)
        info = self.describe_table(source, schema, table)
        metadata_sql = """
            SELECT a.table_type, a.remarks, COALESCE(t.owner_name, v.owner_name)
            FROM v_catalog.all_tables a
            LEFT JOIN v_catalog.tables t
              ON t.table_schema = a.schema_name AND t.table_name = a.table_name
            LEFT JOIN v_catalog.views v
              ON v.table_schema = a.schema_name AND v.table_name = a.table_name
            WHERE a.schema_name = %s AND a.table_name = %s
        """
        projections_sql = """
            SELECT projection_name
            FROM v_catalog.projections
            WHERE anchor_table_schema = %s AND anchor_table_name = %s
            ORDER BY projection_name
        """
        with self._cursor() as cur:
            cur.execute(metadata_sql, (schema, table))
            row = cur.fetchone()
            cur.execute(projections_sql, (schema, table))
            projections = [item[0] for item in cur.fetchall()]
        if not row:
            raise ValueError(f"Unknown table or view: {schema}.{table}")
        object_type, remarks, owner = row
        return TableMetadata(
            source=source,
            schema_name=schema,
            table_name=table,
            object_type=object_type,
            owner=owner,
            remarks=remarks,
            columns=info.columns,
            projections=projections,
            attributes={"adapter": "vertica", "read_only_session": True},
        )

    def get_table_lineage(self, source: str, schema: str, table: str) -> LineageResult:
        self._require_source(source)
        self.describe_table(source, schema, table)
        sql = """
            SELECT reference_table_schema, reference_table_name
            FROM v_catalog.view_tables
            WHERE table_schema = %s AND table_name = %s
            ORDER BY reference_table_schema, reference_table_name
        """
        with self._cursor() as cur:
            cur.execute(sql, (schema, table))
            rows = cur.fetchall()
        subject = f"{source}.{schema}.{table}"
        edges = [
            LineageEdge(
                upstream=f"{source}.{upstream_schema}.{upstream_table}",
                downstream=subject,
            )
            for upstream_schema, upstream_table in rows
        ]
        notes = [
            "Derived from Vertica v_catalog.view_tables. Empty edges mean no view dependency was "
            "reported for this object."
        ]
        return LineageResult(subject=subject, edges=edges, notes=notes)

    def explain_sql(self, source: str, sql: str) -> str:
        self._require_source(source)
        safe_sql = ensure_read_only_sql(sql)
        if safe_sql.lower().startswith("explain "):
            safe_sql = safe_sql.split(None, 1)[1]
        with self._cursor() as cur:
            cur.execute("EXPLAIN " + safe_sql)
            return "\n".join(str(row[0]) for row in cur.fetchall())
