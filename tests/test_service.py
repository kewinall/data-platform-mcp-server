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


def test_operations_and_runbook_search() -> None:
    service = build_service()
    assert service.get_dag_status("quality_checks").state == "failed"
    assert service.search_etl_logs("guardrail")
    assert service.search_runbooks("latency")


def test_demo_explain_is_safe() -> None:
    service = build_service()
    plan = service.explain_sql("analytics", "SELECT * FROM public.orders")
    assert "DEMO PLAN" in plan


def test_capabilities_are_read_only() -> None:
    capabilities = build_service().capabilities()
    assert capabilities["version"] == "0.2.0"
    assert capabilities["safety"] == "read-only"
