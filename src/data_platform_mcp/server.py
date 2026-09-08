from typing import Any

from mcp.server import MCPServer

from data_platform_mcp.config import get_settings
from data_platform_mcp.factory import build_service

settings = get_settings()
service = build_service(settings)
mcp = MCPServer(
    "Data Platform MCP Server",
    instructions=(
        "Read-only Data Engineering/DataOps server. Prefer discovery tools before SQL explain. "
        "Never infer permission to mutate databases or orchestrators from these tools."
    ),
)


@mcp.tool()
def health() -> dict[str, str]:
    """Return MCP server health and version."""
    return service.health()


@mcp.tool()
def list_data_sources() -> list[str]:
    """List data sources that this MCP server can inspect."""
    return service.list_sources()


@mcp.tool()
def list_schemas(source: str) -> list[str]:
    """List schemas in a configured data source."""
    return service.list_schemas(source)


@mcp.tool()
def list_tables(source: str, schema: str) -> list[str]:
    """List tables or views in a schema."""
    return service.list_tables(source, schema)


@mcp.tool()
def describe_table(source: str, schema: str, table: str) -> dict[str, Any]:
    """Describe table columns and data types."""
    return service.describe_table(source, schema, table).model_dump()


@mcp.tool()
def table_statistics(source: str, schema: str, table: str) -> dict[str, Any]:
    """Return lightweight table statistics without reading business rows."""
    return service.table_statistics(source, schema, table).model_dump()


@mcp.tool()
def explain_sql(source: str, sql: str) -> str:
    """Explain a read-only SQL statement. Write/DDL statements are rejected."""
    return service.explain_sql(source, sql)


@mcp.tool()
def list_dags() -> list[dict[str, Any]]:
    """List ETL orchestration DAGs known to the server."""
    return [item.model_dump() for item in service.list_dags()]


@mcp.tool()
def get_dag_status(dag_id: str) -> dict[str, Any]:
    """Return the latest known state of a DAG."""
    return service.get_dag_status(dag_id).model_dump()


@mcp.tool()
def search_etl_logs(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search the configured read-only ETL log backend."""
    safe_limit = max(1, min(limit, settings.max_rows))
    return [item.model_dump() for item in service.search_etl_logs(query, safe_limit)]


@mcp.tool()
def search_runbooks(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search operational runbooks and troubleshooting knowledge."""
    safe_limit = max(1, min(limit, settings.max_rows))
    return [item.model_dump() for item in service.search_runbooks(query, safe_limit)]


@mcp.resource(
    "platform://capabilities",
    title="Data Platform MCP Capabilities",
    description="Active adapters, sources, version, and safety mode.",
    mime_type="application/json",
)
def platform_capabilities() -> dict[str, object]:
    return service.capabilities()


@mcp.resource(
    "catalog://{source}/{schema}/{table}",
    title="Table Catalog Entry",
    description="Read a table's catalog metadata as an MCP resource.",
    mime_type="application/json",
)
def catalog_table(source: str, schema: str, table: str) -> dict[str, Any]:
    return service.describe_table(source, schema, table).model_dump()


@mcp.prompt(
    title="DataOps Incident Triage",
    description="Guide an MCP host through read-only DAG/log/runbook incident triage.",
)
def incident_triage(dag_id: str, symptom: str) -> str:
    return (
        f"Investigate DataOps incident for DAG '{dag_id}'. Symptom: {symptom}. "
        "Use get_dag_status first, then search_etl_logs for concrete evidence, then "
        "search_runbooks for remediation guidance. Distinguish observed facts from "
        "hypotheses. Do not perform write operations."
    )


@mcp.prompt(
    title="Data Discovery",
    description="Guide schema/table discovery before proposing analytics SQL.",
)
def data_discovery(source: str, schema: str, question: str) -> str:
    return (
        f"Answer this data discovery question for source '{source}', schema '{schema}': "
        f"{question}. Use list_tables and describe_table before proposing SQL. If SQL is "
        "needed, keep it read-only and validate it with explain_sql."
    )


def main() -> None:
    if settings.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
