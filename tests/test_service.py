from data_platform_mcp.adapters.demo import (
    DemoCatalogAdapter,
    DemoLogAdapter,
    DemoOperationsAdapter,
    DemoRunbookAdapter,
)
from data_platform_mcp.service import DataPlatformService


def build_service() -> DataPlatformService:
    return DataPlatformService(
        catalog=DemoCatalogAdapter(),
        operations=DemoOperationsAdapter(),
        logs=DemoLogAdapter(),
        runbooks=DemoRunbookAdapter(),
    )


def test_catalog_flow() -> None:
    service = build_service()
    assert service.list_sources() == ["analytics"]
    assert "public" in service.list_schemas("analytics")
    assert "orders" in service.list_tables("analytics", "public")
    table = service.describe_table("analytics", "public", "orders")
    assert table.table_name == "orders"
    assert any(column.name == "amount" for column in table.columns)


def test_metadata_and_lineage_flow() -> None:
    service = build_service()
    metadata = service.get_table_metadata("analytics", "mart", "daily_sales")
    assert metadata.object_type == "VIEW"
    assert metadata.owner == "demo_owner"
    lineage = service.get_table_lineage("analytics", "mart", "daily_sales")
    assert lineage.edges[0].upstream == "analytics.public.orders"

    sql_lineage = service.analyze_sql_lineage(
        "SELECT o.order_id FROM public.orders o JOIN public.customers c "
        "ON c.customer_id = o.customer_id"
    )
    assert sql_lineage.input_tables == ["public.customers", "public.orders"]


def test_operations_and_runbook_search() -> None:
    service = build_service()
    assert service.get_dag_status("quality_checks").state == "failed"
    assert service.search_etl_logs("guardrail")
    assert service.search_runbooks("latency")


def test_demo_explain_is_safe() -> None:
    service = build_service()
    plan = service.explain_sql("analytics", "SELECT * FROM public.orders")
    assert "DEMO PLAN" in plan


def test_capabilities_are_production_delivery_ready() -> None:
    capabilities = build_service().capabilities()
    assert capabilities["version"] == "0.4.0"
    assert capabilities["safety"] == "read-only"
    assert capabilities["sql_policy"] == "sqlglot-ast"
    assert capabilities["multi_tenancy"] is True
    assert capabilities["oidc"] is True
    assert capabilities["opentelemetry"] is True
    assert capabilities["kubernetes"] is True
