import pytest

from data_platform_mcp.security import ensure_read_only_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM public.orders",
        "WITH x AS (SELECT 1) SELECT * FROM x",
        "EXPLAIN SELECT * FROM public.orders",
        "SHOW search_path",
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
    ],
)
def test_write_sql_rejected(sql: str) -> None:
    with pytest.raises(ValueError):
        ensure_read_only_sql(sql)
