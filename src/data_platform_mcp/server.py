import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from data_platform_mcp.audit import AuditLogger
from data_platform_mcp.auth import StaticTokenVerifier, current_principal, require_scope
from data_platform_mcp.config import get_settings
from data_platform_mcp.factory import build_service
from data_platform_mcp.security import sql_fingerprint

T = TypeVar("T")

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
service = build_service(settings)
audit = AuditLogger(enabled=settings.audit_enabled, path=settings.audit_log_path)

mcp_kwargs: dict[str, Any] = {}
if settings.auth_enabled:
    if settings.transport != "streamable-http":
        raise ValueError("DPMCP_AUTH_ENABLED=true requires DPMCP_TRANSPORT=streamable-http")
    if not settings.api_tokens_json:
        raise ValueError("DPMCP_API_TOKENS_JSON is required when bearer authentication is enabled")
    mcp_kwargs["token_verifier"] = StaticTokenVerifier.from_json(
        settings.api_tokens_json,
        settings.auth_resource_url,
    )
    mcp_kwargs["auth"] = AuthSettings(
        issuer_url=AnyHttpUrl(settings.auth_issuer_url),
        resource_server_url=AnyHttpUrl(settings.auth_resource_url),
        required_scopes=["platform:read"],
        validate_token_resource=True,
    )

mcp = MCPServer(
    "Data Platform MCP Server",
    instructions=(
        "Read-only Data Engineering/DataOps server. Prefer discovery and lineage tools before "
        "SQL explain. Never infer permission to mutate databases or orchestrators from these tools."
    ),
    **mcp_kwargs,
)


def _invoke(
    action: str,
    scope: str,
    function: Callable[[], T],
    metadata: dict[str, Any] | None = None,
) -> T:
    started = time.perf_counter()
    principal = current_principal()
    try:
        principal = require_scope(scope)
        result = function()
    except Exception as exc:
        audit.record(
            action=action,
            principal=principal,
            outcome="denied" if isinstance(exc, PermissionError) else "error",
            duration_ms=(time.perf_counter() - started) * 1000,
            metadata=metadata,
            error_type=type(exc).__name__,
        )
        raise
    audit.record(
        action=action,
        principal=principal,
        outcome="success",
        duration_ms=(time.perf_counter() - started) * 1000,
        metadata=metadata,
    )
    return result


@mcp.tool()
def health() -> dict[str, str]:
    """Return MCP server health and version."""
    return _invoke("health", "platform:read", service.health)


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Return the authenticated principal and effective RBAC role/scopes."""

    def resolve() -> dict[str, Any]:
        principal = current_principal()
        return {
            "client_id": principal.client_id,
            "subject": principal.subject,
            "role": principal.role,
            "scopes": list(principal.scopes),
            "auth_enabled": settings.auth_enabled,
        }

    return _invoke("identity.whoami", "platform:read", resolve)


@mcp.tool()
def list_data_sources() -> list[str]:
    """List data sources that this MCP server can inspect."""
    return _invoke("catalog.list_sources", "catalog:read", service.list_sources)


@mcp.tool()
def list_schemas(source: str) -> list[str]:
    """List schemas in a configured data source."""
    return _invoke(
        "catalog.list_schemas",
        "catalog:read",
        lambda: service.list_schemas(source),
        {"source": source},
    )


@mcp.tool()
def list_tables(source: str, schema: str) -> list[str]:
    """List tables or views in a schema."""
    return _invoke(
        "catalog.list_tables",
        "catalog:read",
        lambda: service.list_tables(source, schema),
        {"source": source, "schema": schema},
    )


@mcp.tool()
def describe_table(source: str, schema: str, table: str) -> dict[str, Any]:
    """Describe table columns and data types."""
    return _invoke(
        "catalog.describe_table",
        "catalog:read",
        lambda: service.describe_table(source, schema, table).model_dump(),
        {"source": source, "schema": schema, "table": table},
    )


@mcp.tool()
def table_statistics(source: str, schema: str, table: str) -> dict[str, Any]:
    """Return lightweight table statistics without scanning business rows."""
    return _invoke(
        "catalog.table_statistics",
        "catalog:read",
        lambda: service.table_statistics(source, schema, table).model_dump(),
        {"source": source, "schema": schema, "table": table},
    )


@mcp.tool()
def get_table_metadata(source: str, schema: str, table: str) -> dict[str, Any]:
    """Return governed table metadata such as object type, owner, columns, and projections."""
    return _invoke(
        "metadata.get_table",
        "catalog:read",
        lambda: service.get_table_metadata(source, schema, table).model_dump(),
        {"source": source, "schema": schema, "table": table},
    )


@mcp.tool()
def get_table_lineage(source: str, schema: str, table: str) -> dict[str, Any]:
    """Return catalog-backed upstream lineage for a table or view."""
    return _invoke(
        "lineage.get_table",
        "lineage:read",
        lambda: service.get_table_lineage(source, schema, table).model_dump(),
        {"source": source, "schema": schema, "table": table},
    )


@mcp.tool()
def analyze_sql_lineage(sql: str) -> dict[str, Any]:
    """Parse read-only SQL and extract referenced input tables and CTEs."""
    return _invoke(
        "lineage.analyze_sql",
        "lineage:read",
        lambda: service.analyze_sql_lineage(sql).model_dump(),
        {"sql_fingerprint": sql_fingerprint(sql)},
    )


@mcp.tool()
def explain_sql(source: str, sql: str) -> str:
    """Explain a read-only SQL statement after SQLGlot AST policy validation."""
    return _invoke(
        "sql.explain",
        "sql:explain",
        lambda: service.explain_sql(source, sql),
        {"source": source, "sql_fingerprint": sql_fingerprint(sql)},
    )


@mcp.tool()
def list_dags() -> list[dict[str, Any]]:
    """List ETL orchestration DAGs known to the server."""
    return _invoke(
        "operations.list_dags",
        "operations:read",
        lambda: [item.model_dump() for item in service.list_dags()],
    )


@mcp.tool()
def get_dag_status(dag_id: str) -> dict[str, Any]:
    """Return the latest known state of a DAG."""
    return _invoke(
        "operations.get_dag_status",
        "operations:read",
        lambda: service.get_dag_status(dag_id).model_dump(),
        {"dag_id": dag_id},
    )


@mcp.tool()
def search_etl_logs(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search the configured read-only ETL log backend."""
    safe_limit = max(1, min(limit, settings.max_rows))
    return _invoke(
        "logs.search",
        "logs:read",
        lambda: [item.model_dump() for item in service.search_etl_logs(query, safe_limit)],
        {"query_length": len(query), "limit": safe_limit},
    )


@mcp.tool()
def search_runbooks(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search operational runbooks and troubleshooting knowledge."""
    safe_limit = max(1, min(limit, settings.max_rows))
    return _invoke(
        "runbook.search",
        "runbook:read",
        lambda: [item.model_dump() for item in service.search_runbooks(query, safe_limit)],
        {"query_length": len(query), "limit": safe_limit},
    )


@mcp.resource(
    "platform://capabilities",
    title="Data Platform MCP Capabilities",
    description="Active adapters, sources, version, auth, audit, and safety mode.",
    mime_type="application/json",
)
def platform_capabilities() -> dict[str, object]:
    def resolve() -> dict[str, object]:
        capabilities = service.capabilities()
        capabilities.update(
            {
                "auth_enabled": settings.auth_enabled,
                "audit_enabled": settings.audit_enabled,
            }
        )
        return capabilities

    return _invoke("resource.capabilities", "platform:read", resolve)


@mcp.resource(
    "catalog://{source}/{schema}/{table}",
    title="Table Catalog Entry",
    description="Read a governed table metadata entry as an MCP resource.",
    mime_type="application/json",
)
def catalog_table(source: str, schema: str, table: str) -> dict[str, Any]:
    return _invoke(
        "resource.catalog_table",
        "catalog:read",
        lambda: service.get_table_metadata(source, schema, table).model_dump(),
        {"source": source, "schema": schema, "table": table},
    )


@mcp.prompt(
    title="DataOps Incident Triage",
    description="Guide an MCP host through read-only DAG/log/runbook incident triage.",
)
def incident_triage(dag_id: str, symptom: str) -> str:
    return _invoke(
        "prompt.incident_triage",
        "operations:read",
        lambda: (
            f"Investigate DataOps incident for DAG '{dag_id}'. Symptom: {symptom}. "
            "Use get_dag_status first, then search_etl_logs for concrete evidence, then "
            "search_runbooks for remediation guidance. Distinguish observed facts from "
            "hypotheses. Do not perform write operations."
        ),
        {"dag_id": dag_id, "symptom_length": len(symptom)},
    )


@mcp.prompt(
    title="Data Discovery",
    description="Guide metadata and lineage discovery before proposing analytics SQL.",
)
def data_discovery(source: str, schema: str, question: str) -> str:
    return _invoke(
        "prompt.data_discovery",
        "catalog:read",
        lambda: (
            f"Answer this data discovery question for source '{source}', schema '{schema}': "
            f"{question}. Use list_tables, get_table_metadata, and get_table_lineage before "
            "proposing SQL. If SQL is needed, keep it read-only, inspect dependencies with "
            "analyze_sql_lineage, and validate it with explain_sql."
        ),
        {"source": source, "schema": schema, "question_length": len(question)},
    )


def main() -> None:
    if settings.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
