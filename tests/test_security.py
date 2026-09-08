import pytest

from data_platform_mcp.lineage import analyze_sql_lineage
from data_platform_mcp.security import ensure_read_only_sql, sql_fingerprint


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM public.orders",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "EXPLAIN SELECT * FROM public.orders",
        "SHOW search_path",
        "SELECT customer_id FROM public.orders UNION ALL SELECT customer_id FROM public.customers",
    ],
)
def test_read_only_sql_allowed(sql: str) -> None:
    assert ensure_read_only_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "UPDATE orders SET amount = 0",
        "DROP TABLE orders",
        "SELECT 1; DELETE FROM orders",
        "SELECT * INTO temp_orders FROM public.orders",
        "WITH changed AS (DELETE FROM orders RETURNING *) SELECT * FROM changed",
    ],
)
def test_write_sql_rejected(sql: str) -> None:
    with pytest.raises(ValueError):
        ensure_read_only_sql(sql)


def test_sql_lineage_extracts_real_inputs_and_excludes_cte_alias() -> None:
    result = analyze_sql_lineage(
        "WITH recent AS (SELECT * FROM public.orders) "
        "SELECT * FROM recent JOIN mart.customers c ON c.customer_id = recent.customer_id"
    )
    assert result.input_tables == ["mart.customers", "public.orders"]
    assert result.ctes == ["recent"]


def test_sql_fingerprint_is_stable_without_exposing_sql() -> None:
    first = sql_fingerprint("SELECT *   FROM public.orders")
    second = sql_fingerprint("SELECT * FROM public.orders")
    assert first == second
    assert "orders" not in first
    assert len(first) == 16
