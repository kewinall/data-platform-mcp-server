from contextlib import closing

import psycopg

from data_platform_mcp.models import ColumnInfo, TableInfo, TableStatistics
from data_platform_mcp.security import ensure_read_only_sql


class PostgresCatalogAdapter:
    """Read-only PostgreSQL catalog adapter.

    Use a database account that has SELECT/catalog privileges only. The server also
    enforces read-only SQL, but database-side least privilege remains mandatory.
    """

    def __init__(self, dsn: str, statement_timeout_ms: int = 5000):
        self.dsn = dsn
        self.statement_timeout_ms = statement_timeout_ms

    def _connect(self):
        return psycopg.connect(
            self.dsn,
            options=(
                "-c default_transaction_read_only=on "
                f"-c statement_timeout={self.statement_timeout_ms}"
            ),
        )

    def list_sources(self) -> list[str]:
        return ["postgres"]

    def _require_source(self, source: str) -> None:
        if source != "postgres":
            raise ValueError("PostgreSQL adapter exposes source name 'postgres'")

    def list_schemas(self, source: str) -> list[str]:
        self._require_source(source)
        sql = """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema'
            ORDER BY schema_name
        """
        with closing(self._connect()) as conn, conn.cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in cur.fetchall()]

    def list_tables(self, source: str, schema: str) -> list[str]:
        self._require_source(source)
        sql = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type IN ('BASE TABLE', 'VIEW')
            ORDER BY table_name
        """
        with closing(self._connect()) as conn, conn.cursor() as cur:
            cur.execute(sql, (schema,))
            return [row[0] for row in cur.fetchall()]

    def describe_table(self, source: str, schema: str, table: str) -> TableInfo:
        self._require_source(source)
        sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        with closing(self._connect()) as conn, conn.cursor() as cur:
            cur.execute(sql, (schema, table))
            rows = cur.fetchall()
        if not rows:
            raise ValueError(f"Unknown table: {schema}.{table}")
        return TableInfo(
            schema_name=schema,
            table_name=table,
            columns=[
                ColumnInfo(name=name, data_type=data_type, nullable=nullable == "YES")
                for name, data_type, nullable in rows
            ],
        )

    def table_statistics(self, source: str, schema: str, table: str) -> TableStatistics:
        self._require_source(source)
        self.describe_table(source, schema, table)
        sql = """
            SELECT c.reltuples::bigint
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = %s
        """
        with closing(self._connect()) as conn, conn.cursor() as cur:
            cur.execute(sql, (schema, table))
            row = cur.fetchone()
        return TableStatistics(
            schema_name=schema,
            table_name=table,
            row_count=row[0] if row else None,
            notes=["row_count is the PostgreSQL planner estimate (pg_class.reltuples)."],
        )

    def explain_sql(self, source: str, sql: str) -> str:
        self._require_source(source)
        safe_sql = ensure_read_only_sql(sql)
        with closing(self._connect()) as conn, conn.cursor() as cur:
            cur.execute("EXPLAIN (FORMAT TEXT) " + safe_sql)
            return "\n".join(row[0] for row in cur.fetchall())
