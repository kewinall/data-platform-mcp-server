from data_platform_mcp.adapters.base import (
    CatalogAdapter,
    LogSearchAdapter,
    OperationsAdapter,
    RunbookAdapter,
)
from data_platform_mcp.models import DagInfo, SearchHit, TableInfo, TableStatistics


class DataPlatformService:
    def __init__(
        self,
        catalog: CatalogAdapter,
        operations: OperationsAdapter,
        logs: LogSearchAdapter,
        runbooks: RunbookAdapter,
    ):
        self.catalog = catalog
        self.operations = operations
        self.logs = logs
        self.runbooks = runbooks

    def health(self) -> dict[str, str]:
        return {"status": "ok", "service": "data-platform-mcp-server", "version": "0.2.0"}

    def capabilities(self) -> dict[str, object]:
        return {
            "version": "0.2.0",
            "catalog_sources": self.catalog.list_sources(),
            "operations_adapter": type(self.operations).__name__,
            "log_adapter": type(self.logs).__name__,
            "safety": "read-only",
        }

    def list_sources(self) -> list[str]:
        return self.catalog.list_sources()

    def list_schemas(self, source: str) -> list[str]:
        return self.catalog.list_schemas(source)

    def list_tables(self, source: str, schema: str) -> list[str]:
        return self.catalog.list_tables(source, schema)

    def describe_table(self, source: str, schema: str, table: str) -> TableInfo:
        return self.catalog.describe_table(source, schema, table)

    def table_statistics(self, source: str, schema: str, table: str) -> TableStatistics:
        return self.catalog.table_statistics(source, schema, table)

    def explain_sql(self, source: str, sql: str) -> str:
        return self.catalog.explain_sql(source, sql)

    def list_dags(self) -> list[DagInfo]:
        return self.operations.list_dags()

    def get_dag_status(self, dag_id: str) -> DagInfo:
        return self.operations.get_dag_status(dag_id)

    def search_etl_logs(self, query: str, limit: int = 10) -> list[SearchHit]:
        return self.logs.search(query, limit)

    def search_runbooks(self, query: str, limit: int = 10) -> list[SearchHit]:
        return self.runbooks.search(query, limit)
