from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DPMCP_", extra="ignore")

    mode: Literal["demo", "postgres", "vertica", "multi"] = "demo"
    operations_mode: Literal["demo", "airflow"] = "demo"
    logs_mode: Literal["demo", "opensearch", "loki"] = "demo"

    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    max_rows: int = 100

    postgres_dsn: str | None = None
    postgres_statement_timeout_ms: int = 5000

    vertica_dsn: str | None = None
    vertica_source_name: str = "vertica"
    vertica_connection_timeout_seconds: float = 10.0
    vertica_session_label: str = "data-platform-mcp"

    airflow_base_url: str | None = None
    airflow_token: str | None = None
    airflow_timeout_seconds: float = 10.0

    opensearch_url: str | None = None
    opensearch_index: str = "etl-logs-*"
    opensearch_username: str | None = None
    opensearch_password: str | None = None
    opensearch_token: str | None = None

    loki_url: str | None = None
    loki_token: str | None = None
    loki_query: str = '{job=~".+"} |= "{query}"'

    auth_enabled: bool = False
    auth_mode: Literal["static", "oidc"] = "static"
    auth_issuer_url: str = "https://auth.example.com"
    auth_resource_url: str = "http://127.0.0.1:8000/mcp"
    api_tokens_json: str | None = None

    oidc_jwks_url: str | None = None
    oidc_audience: str | None = None
    oidc_algorithms: str = "RS256"
    oidc_role_claim: str = "roles"
    oidc_tenant_claim: str = "tenant"
    oidc_client_id_claim: str = "azp"
    oidc_role_map_json: str | None = None

    tenant_enabled: bool = False
    tenant_allowed_sources_json: str | None = None

    audit_enabled: bool = True
    audit_log_path: str | None = None

    otel_enabled: bool = False
    otel_service_name: str = "data-platform-mcp-server"
    otel_exporter_otlp_endpoint: str | None = None
    otel_metric_export_interval_ms: int = 60000
    deployment_environment: str = "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
