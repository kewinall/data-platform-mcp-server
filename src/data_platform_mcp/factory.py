from data_platform_mcp.adapters.demo import (
    DemoCatalogAdapter,
    DemoOperationsAdapter,
    DemoRunbookAdapter,
)
from data_platform_mcp.adapters.postgres import PostgresCatalogAdapter
from data_platform_mcp.config import Settings
from data_platform_mcp.service import DataPlatformService


def build_service(settings: Settings) -> DataPlatformService:
    if settings.mode == "postgres":
        if not settings.postgres_dsn:
            raise ValueError("DPMCP_POSTGRES_DSN is required when DPMCP_MODE=postgres")
        catalog = PostgresCatalogAdapter(
            settings.postgres_dsn,
            statement_timeout_ms=settings.postgres_statement_timeout_ms,
        )
    else:
        catalog = DemoCatalogAdapter()

    # Airflow remains opt-in in v0.1; demo operations guarantee a zero-dependency demo.
    operations = DemoOperationsAdapter()
    runbooks = DemoRunbookAdapter()
    return DataPlatformService(catalog=catalog, operations=operations, runbooks=runbooks)
