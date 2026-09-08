# Architecture / 架構

## 繁體中文

`data-platform-mcp-server` 的核心原則是把「AI Agent 可呼叫的能力」與「實際資料平台實作」分離。MCP Tool 只依賴 `DataPlatformService`，Service 再透過 Adapter 存取不同後端。

v0.1 預設使用 Demo Adapter，因此 CI、面試展示與本機測試不需要任何企業環境。PostgreSQL Adapter 則示範如何以唯讀帳號、安全 SQL Policy 與 Statement Timeout 接入真實資料庫。

## English

The project separates MCP-facing capabilities from backend-specific integrations. MCP tools call `DataPlatformService`, while adapters encapsulate the data platform implementation.

v0.1 defaults to synthetic demo adapters so CI and demos never require enterprise infrastructure. The PostgreSQL adapter demonstrates a production-oriented read-only integration using least-privileged credentials, SQL policy enforcement, and statement timeouts.

## Components

```text
MCP Host
  -> MCPServer
    -> DataPlatformService
      -> CatalogAdapter
      -> OperationsAdapter
      -> RunbookAdapter
```

## Adapter roadmap

| Adapter | v0.1 | Planned |
|---|---:|---|
| Synthetic Demo | ✅ | Keep for CI/demo |
| PostgreSQL | ✅ catalog | richer stats |
| Airflow 3 | scaffold | DAG run/task/log integration |
| Vertica | — | schema/catalog/query profile |
| OpenSearch/Loki | — | centralized log search |
| GitLab/Runbook | — | controlled knowledge search |
