from data_platform_mcp.adapters.airflow import AirflowOperationsAdapter
from data_platform_mcp.adapters.composite import CompositeCatalogAdapter
from data_platform_mcp.adapters.demo import (
    DemoCatalogAdapter,
    DemoLogAdapter,
    DemoOperationsAdapter,
    DemoRunbookAdapter,
)
from data_platform_mcp.adapters.etl_metadata import (
    DemoETLMetadataAdapter,
    FileETLMetadataAdapter,
)
from data_platform_mcp.adapters.logs import LokiLogAdapter, OpenSearchLogAdapter
from data_platform_mcp.adapters.postgres import PostgresCatalogAdapter
from data_platform_mcp.adapters.vertica import VerticaCatalogAdapter
from data_platform_mcp.config import Settings
from data_platform_mcp.service import DataPlatformService


def _postgres(settings: Settings) -> PostgresCatalogAdapter:
    if not settings.postgres_dsn:
        raise ValueError("DPMCP_POSTGRES_DSN is required for the PostgreSQL catalog adapter")
    return PostgresCatalogAdapter(
        settings.postgres_dsn,
        statement_timeout_ms=settings.postgres_statement_timeout_ms,
    )


def _vertica(settings: Settings) -> VerticaCatalogAdapter:
    if not settings.vertica_dsn:
        raise ValueError("DPMCP_VERTICA_DSN is required for the Vertica catalog adapter")
    return VerticaCatalogAdapter(
        settings.vertica_dsn,
        source_name=settings.vertica_source_name,
        connection_timeout=settings.vertica_connection_timeout_seconds,
        session_label=settings.vertica_session_label,
    )


def build_service(settings: Settings) -> DataPlatformService:
    if settings.mode == "postgres":
        catalog = _postgres(settings)
    elif settings.mode == "vertica":
        catalog = _vertica(settings)
    elif settings.mode == "multi":
        adapters = []
        if settings.postgres_dsn:
            adapters.append(_postgres(settings))
        if settings.vertica_dsn:
            adapters.append(_vertica(settings))
        if not adapters:
            raise ValueError(
                "DPMCP_MODE=multi requires DPMCP_POSTGRES_DSN and/or DPMCP_VERTICA_DSN"
            )
        catalog = CompositeCatalogAdapter(adapters)
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

    if settings.etl_metadata_dir:
        etl_metadata = FileETLMetadataAdapter(
            settings.etl_metadata_dir,
            max_files=settings.etl_metadata_max_files,
        )
    else:
        etl_metadata = DemoETLMetadataAdapter()

    return DataPlatformService(
        catalog=catalog,
        operations=operations,
        logs=logs,
        runbooks=DemoRunbookAdapter(),
        etl_metadata=etl_metadata,
    )
