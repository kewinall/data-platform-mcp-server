from data_platform_mcp.adapters.vertica import VerticaCatalogAdapter


class FakeCursor:
    def __init__(self, statements: list[tuple[str, object]]):
        self.statements = statements
        self.rows: list[tuple] = []

    def execute(self, sql: str, params=None) -> None:
        normalized = " ".join(sql.split())
        self.statements.append((normalized, params))
        if normalized.startswith("SET SESSION CHARACTERISTICS"):
            self.rows = []
        elif "FROM v_catalog.schemata" in normalized:
            self.rows = [("mart",), ("public",)]
        elif "FROM v_catalog.columns" in normalized:
            self.rows = [("order_id", "int", False, 1), ("amount", "numeric(12,2)", True, 2)]
        elif "FROM v_catalog.all_tables a" in normalized:
            self.rows = [("TABLE", "Orders fact table", "readonly_owner")]
        elif "FROM v_catalog.projections" in normalized and "anchor_table_schema" in normalized:
            self.rows = [("orders_super",)]
        elif "FROM v_catalog.view_tables" in normalized:
            self.rows = [("public", "orders")]
        elif normalized.startswith("EXPLAIN "):
            self.rows = [("Access Path:",), ("STORAGE ACCESS for orders",)]
        else:
            self.rows = []

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self) -> None:
        return None


class FakeConnection:
    def __init__(self, statements: list[tuple[str, object]]):
        self.statements = statements

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.statements)

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_vertica_catalog_uses_read_only_session_and_metadata() -> None:
    statements: list[tuple[str, object]] = []

    def connect_fn(**kwargs):
        assert kwargs["dsn"].startswith("vertica://")
        assert kwargs["autocommit"] is False
        return FakeConnection(statements)

    adapter = VerticaCatalogAdapter(
        "vertica://readonly@db.example:5433/analytics",
        connect_fn=connect_fn,
    )

    assert adapter.list_schemas("vertica") == ["mart", "public"]
    metadata = adapter.get_table_metadata("vertica", "public", "orders")
    assert metadata.owner == "readonly_owner"
    assert metadata.projections == ["orders_super"]
    assert metadata.attributes["read_only_session"] is True

    readonly_statements = [sql for sql, _ in statements if sql.startswith("SET SESSION")]
    assert len(readonly_statements) >= 2


def test_vertica_lineage_and_explain_are_read_only() -> None:
    statements: list[tuple[str, object]] = []
    adapter = VerticaCatalogAdapter(
        "vertica://readonly@db.example:5433/analytics",
        connect_fn=lambda **kwargs: FakeConnection(statements),
    )

    lineage = adapter.get_table_lineage("vertica", "mart", "daily_sales")
    assert lineage.edges[0].upstream == "vertica.public.orders"
    assert lineage.edges[0].downstream == "vertica.mart.daily_sales"

    plan = adapter.explain_sql("vertica", "SELECT * FROM public.orders")
    assert "STORAGE ACCESS" in plan
