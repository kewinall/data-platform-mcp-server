from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DPMCP_", extra="ignore")

    mode: Literal["demo", "postgres"] = "demo"
    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    postgres_dsn: str | None = None
    postgres_statement_timeout_ms: int = 5000

    airflow_base_url: str | None = None
    airflow_token: str | None = None
    airflow_timeout_seconds: float = 10.0

    max_rows: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
