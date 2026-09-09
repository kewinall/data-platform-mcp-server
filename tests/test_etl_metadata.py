import json
from pathlib import Path

import pytest

from data_platform_mcp.adapters.etl_metadata import (
    DemoETLMetadataAdapter,
    FileETLMetadataAdapter,
)


def test_demo_etl_metadata_contract_is_read_only_and_classified() -> None:
    adapter = DemoETLMetadataAdapter()
    pipeline = adapter.get_pipeline("legacy_order_enrichment")
    assert pipeline["schema_version"] == "1.1"
    assert pipeline["lineage"]["structural"]
    assert pipeline["lineage"]["inferred"]
    assert pipeline["lineage"]["ai_interpretation"] == []

    pipeline["steps"].clear()
    assert adapter.get_pipeline_steps("legacy_order_enrichment")


def test_etl_metadata_search_and_table_lineage() -> None:
    adapter = DemoETLMetadataAdapter()
    assert adapter.search("orders")
    lineage = adapter.get_table_lineage("analytics.orders_enriched")
    assert lineage["edges"]
    assert any(
        edge["classification"] == "inferred-deterministic"
        for edge in lineage["edges"]
    )
    assert "MCP exposes the contract" in lineage["authority"]


def test_file_adapter_loads_exported_contract(tmp_path: Path) -> None:
    payload = DemoETLMetadataAdapter().get_pipeline("legacy_order_enrichment")
    (tmp_path / "pipeline.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    adapter = FileETLMetadataAdapter(tmp_path)
    assert adapter.list_pipelines() == ["legacy_order_enrichment"]


def test_file_adapter_rejects_unsupported_contract(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text(
        '{"schema_version":"9.9","pipeline":{"id":"bad"}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unsupported ETL metadata"):
        FileETLMetadataAdapter(tmp_path)
