from data_platform_mcp.adapters.airflow import AirflowOperationsAdapter
from data_platform_mcp.adapters.demo import (
    DemoCatalogAdapter,
    DemoLogAdapter,
    DemoOperationsAdapter,
    DemoRunbookAdapter,
)
from data_platform_mcp.adapters.logs import LokiLogAdapter, OpenSearchLogAdapter
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

    if settings.operations_mode == "airflow":
        if not settings.airflow_base_url:
            raise ValueError(
                "DPMCP_AIRFLOW_BASE_URL is required when DPMCP_OPERATIONS_MODE=airflow"
            )
        operations = AirflowOperationsAdapter(
            settings.airflow_base_url,
            token=settings.airflow_token,
            timeout=settings.airflow_timeout_seconds,
        )
    else:
        operations = DemoOperationsAdapter()

    if settings.logs_mode == "opensearch":
        if not settings.opensearch_url:
            raise ValueError(
                "DPMCP_OPENSEARCH_URL is required when DPMCP_LOGS_MODE=opensearch"
            )
        logs = OpenSearchLogAdapter(
            settings.opensearch_url,
            settings.opensearch_index,
            username=settings.opensearch_username,
            password=settings.opensearch_password,
            token=settings.opensearch_token,
        )
    elif settings.logs_mode == "loki":
        if not settings.loki_url:
            raise ValueError("DPMCP_LOKI_URL is required when DPMCP_LOGS_MODE=loki")
        logs = LokiLogAdapter(
            settings.loki_url,
            settings.loki_query,
            token=settings.loki_token,
        )
    else:
        logs = DemoLogAdapter()

    return DataPlatformService(
        catalog=catalog,
        operations=operations,
        logs=logs,
        runbooks=DemoRunbookAdapter(),
    )
