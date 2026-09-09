# ETL Metadata Integration / ETL Metadata 整合

## 繁體中文

### Responsibility boundary

~~~text
enterprise-etl-platform
  Pentaho / Hop parser
  normalized metadata
  lineage classification
  migration validation
          |
          | JSON contract (read-only)
          v
data-platform-mcp-server
  auth / scopes / audit
  MCP tool + resource contract
          |
          +--> Agentic DataOps Copilot
          +--> Other MCP hosts
~~~

data-platform-mcp-server **不解析 Pentaho KTR/KJB 或 Apache Hop artifact**。它只讀取 enterprise-etl-platform 已產生的 normalized metadata。

這可避免 MCP integration layer 成為第二份 ETL source of truth。

### Configuration

未設定時，Server 使用 synthetic demo ETL metadata contract。

要讀取 ETL producer 匯出的 JSON：

~~~bash
export DPMCP_ETL_METADATA_DIR=/srv/etl-metadata
export DPMCP_ETL_METADATA_MAX_FILES=500
data-platform-mcp
~~~

正式部署應將該目錄以 read-only volume 或受控 artifact sync 掛載。

### MCP tools

| Tool | Scope | Purpose |
|---|---|---|
| list_etl_pipelines | catalog:read | list normalized ETL pipeline IDs |
| get_etl_pipeline | catalog:read | full normalized producer contract |
| get_etl_pipeline_steps | catalog:read | deterministic step metadata |
| get_etl_pipeline_dependencies | lineage:read | producer dependency records |
| get_etl_table_lineage | lineage:read | producer lineage edges + capability boundary |
| search_etl_metadata | catalog:read | search pipeline/step/table/dependency names |

Resource:

~~~text
etl://pipeline/{pipeline_id}
~~~

### Lineage semantics

Adapter 保留 producer classification：

- structural
- inferred-deterministic
- AI interpretation

MCP layer 不會把 AI interpretation 升格成 deterministic lineage，也不會自行補出缺少的 edge。

get_etl_table_lineage 會回傳 producer 的 capability boundaries，讓 consumer 知道目前是否具備完整 column-level lineage。

### Failure / recovery

| Failure | Behavior | Recovery |
|---|---|---|
| invalid JSON / unsupported schema | adapter startup fails closed | 重新發布符合 contract 的 producer artifact |
| unknown pipeline | bounded error | 先用 list/search discovery |
| producer export unavailable | 不以 MCP inference 取代 truth | 恢復 artifact publication |
| incomplete column lineage | 回傳 capability boundary | 改善 producer parser，不在 MCP 猜測 |
| MCP unavailable | ETL producer truth 不受影響 | 恢復 MCP service |

### Security / governance

- 不提供 ETL mutation tool。
- 既有 authentication、RBAC scope、audit、OpenTelemetry 仍包住每個 tool invocation。
- Caller 不能指定任意 filesystem path；directory 是 deployment configuration。
- 原始 Pentaho/Hop parsing 維持在 ETL repository。
- shared multi-tenant deployment 若要共用不同 tenant 的 ETL metadata，應先增加明確 tenant-aware artifact policy；在此之前建議使用隔離的 artifact source / MCP deployment。

## English

This integration exposes normalized ETL metadata produced by enterprise-etl-platform through governed read-only MCP tools and a resource.

The MCP repository does not duplicate Pentaho/Hop parsing, migration conversion, or lineage generation. It preserves producer lineage classifications and capability boundaries so consumers can distinguish deterministic truth from inference and AI interpretation.
