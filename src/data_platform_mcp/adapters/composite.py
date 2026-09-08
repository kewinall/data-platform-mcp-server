from data_platform_mcp.adapters.base import CatalogAdapter
from data_platform_mcp.models import LineageResult, TableInfo, TableMetadata, TableStatistics


class CompositeCatalogAdapter:
    """Route catalog calls across multiple adapters by exposed source name."""

    def __init__(self, adapters: list[CatalogAdapter]):
        if not adapters:
            raise ValueError("CompositeCatalogAdapter requires at least one adapter")
        self.adapters = adapters
        self._routes: dict[str, CatalogAdapter] = {}
        for adapter in adapters:
            for source in adapter.list_sources():
                if source in self._routes:
                    raise ValueError(f"Duplicate catalog source name: {source}")
                self._routes[source] = adapter

    def list_sources(self) -> list[str]:
        return sorted(self._routes)

    def _adapter(self, source: str) -> CatalogAdapter:
        try:
            return self._routes[source]
        except KeyError as exc:
            raise ValueError(f"Unknown source: {source}") from exc

    def list_schemas(self, source: str) -> list[str]:
        return self._adapter(source).list_schemas(source)

    def list_tables(self, source: str, schema: str) -> list[str]:
        return self._adapter(source).list_tables(source, schema)

    def describe_table(self, source: str, schema: str, table: str) -> TableInfo:
        return self._adapter(source).describe_table(source, schema, table)

    def table_statistics(self, source: str, schema: str, table: str) -> TableStatistics:
        return self._adapter(source).table_statistics(source, schema, table)

    def get_table_metadata(self, source: str, schema: str, table: str) -> TableMetadata:
        return self._adapter(source).get_table_metadata(source, schema, table)

    def get_table_lineage(self, source: str, schema: str, table: str) -> LineageResult:
        return self._adapter(source).get_table_lineage(source, schema, table)

    def explain_sql(self, source: str, sql: str) -> str:
        return self._adapter(source).explain_sql(source, sql)
