"""Read-only adapter for normalized ETL metadata exported by enterprise-etl-platform."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def _pipeline_id(document: dict[str, Any]) -> str:
    pipeline = document.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ValueError("ETL metadata document is missing pipeline")
    value = pipeline.get("id") or pipeline.get("name")
    if not value:
        raise ValueError("ETL metadata document is missing pipeline id/name")
    return str(value)


def _validate_document(document: dict[str, Any]) -> dict[str, Any]:
    version = str(document.get("schema_version") or "")
    if not version.startswith("1."):
        raise ValueError(f"Unsupported ETL metadata schema_version: {version!r}")
    _pipeline_id(document)
    lineage = document.get("lineage")
    if lineage is not None and not isinstance(lineage, dict):
        raise ValueError("ETL metadata lineage must be an object")
    return document


def _table_endpoint(value: Any) -> str | None:
    text = str(value or "")
    if text.startswith("table:"):
        return text[6:]
    return None


class ETLMetadataAdapter:
    """In-memory read-only view over producer-owned normalized metadata documents."""

    def __init__(self, documents: list[dict[str, Any]]):
        self._documents: dict[str, dict[str, Any]] = {}
        for raw in documents:
            document = _validate_document(deepcopy(raw))
            key = _pipeline_id(document)
            if key in self._documents:
                raise ValueError(f"Duplicate ETL pipeline id: {key}")
            self._documents[key] = document

    def list_pipelines(self) -> list[str]:
        return sorted(self._documents)

    def get_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        try:
            return deepcopy(self._documents[pipeline_id])
        except KeyError as exc:
            raise ValueError(f"Unknown ETL pipeline: {pipeline_id}") from exc

    def get_pipeline_steps(self, pipeline_id: str) -> list[dict[str, Any]]:
        document = self.get_pipeline(pipeline_id)
        return deepcopy(document.get("steps", []))

    def get_pipeline_dependencies(self, pipeline_id: str) -> list[dict[str, Any]]:
        document = self.get_pipeline(pipeline_id)
        return deepcopy(document.get("dependencies", []))

    def get_table_lineage(self, table: str) -> dict[str, Any]:
        edges: list[dict[str, Any]] = []
        boundaries: list[str] = []
        for pipeline_id, document in self._documents.items():
            lineage = document.get("lineage") or {}
            for group in ("structural", "inferred"):
                for edge in lineage.get(group, []):
                    upstream = _table_endpoint(edge.get("from"))
                    downstream = _table_endpoint(edge.get("to"))
                    if table not in {upstream, downstream}:
                        continue
                    item = deepcopy(edge)
                    item["pipeline_id"] = pipeline_id
                    item["lineage_group"] = group
                    edges.append(item)
            boundaries.extend(
                str(item)
                for item in document.get("capability_boundaries", [])
                if item
            )
        return {
            "table": table,
            "edges": edges,
            "capability_boundaries": list(dict.fromkeys(boundaries)),
            "authority": (
                "producer-owned ETL metadata; MCP exposes the contract and does not "
                "create new lineage facts"
            ),
        }

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        needle = query.lower().strip()
        if not needle:
            return []
        results: list[dict[str, Any]] = []
        for pipeline_id, document in sorted(self._documents.items()):
            pipeline = document.get("pipeline") or {}
            steps = document.get("steps") or []
            tables = document.get("tables") or []
            dependencies = document.get("dependencies") or []
            searchable = [
                pipeline_id,
                str(pipeline.get("name") or ""),
                *(str(item.get("name") or "") for item in steps),
                *(str(item.get("type") or "") for item in steps),
                *(str(item.get("name") or "") for item in tables),
                *(str(item.get("from") or "") for item in dependencies),
                *(str(item.get("to") or "") for item in dependencies),
            ]
            matched = sorted(
                {value for value in searchable if needle in value.lower()}
            )
            if not matched:
                continue
            results.append(
                {
                    "pipeline_id": pipeline_id,
                    "pipeline_name": pipeline.get("name"),
                    "schema_version": document.get("schema_version"),
                    "matched_values": matched[:10],
                    "step_count": len(steps),
                    "table_count": len(tables),
                }
            )
            if len(results) >= limit:
                break
        return results


class FileETLMetadataAdapter(ETLMetadataAdapter):
    """Load JSON metadata artifacts from an explicitly configured directory."""

    def __init__(self, directory: str | Path, max_files: int = 500):
        root = Path(directory).expanduser()
        if not root.is_dir():
            raise ValueError(f"ETL metadata directory does not exist: {root}")
        paths = sorted(root.rglob("*.json"))
        if len(paths) > max_files:
            raise ValueError(
                f"ETL metadata directory contains {len(paths)} JSON files; "
                f"max is {max_files}"
            )
        documents: list[dict[str, Any]] = []
        for path in paths:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid ETL metadata JSON: {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"ETL metadata document must be an object: {path}")
            documents.append(payload)
        super().__init__(documents)


class DemoETLMetadataAdapter(ETLMetadataAdapter):
    """Synthetic metadata contract for demos and MCP protocol tests."""

    def __init__(self):
        super().__init__(
            [
                {
                    "schema_version": "1.1",
                    "pipeline": {
                        "id": "legacy_order_enrichment",
                        "name": "legacy_order_enrichment",
                        "kind": "pentaho-transformation",
                        "format": "pentaho-xml",
                        "source_path": "synthetic/legacy_order_enrichment.ktr",
                    },
                    "steps": [
                        {
                            "id": "step-0001",
                            "name": "Read Orders",
                            "type": "TableInput",
                        },
                        {
                            "id": "step-0002",
                            "name": "Write Orders",
                            "type": "TableOutput",
                        },
                    ],
                    "tables": [
                        {"name": "staging.orders", "role": "source"},
                        {"name": "analytics.orders_enriched", "role": "target"},
                    ],
                    "dependencies": [
                        {
                            "kind": "step",
                            "from": "step-0001",
                            "to": "step-0002",
                            "classification": "structural",
                        }
                    ],
                    "lineage": {
                        "structural": [
                            {
                                "kind": "reads_from",
                                "from": "table:staging.orders",
                                "to": "step:step-0001",
                                "classification": "structural",
                            },
                            {
                                "kind": "writes_to",
                                "from": "step:step-0002",
                                "to": "table:analytics.orders_enriched",
                                "classification": "structural",
                            },
                        ],
                        "inferred": [
                            {
                                "kind": "table_flow",
                                "from": "table:staging.orders",
                                "to": "table:analytics.orders_enriched",
                                "classification": "inferred-deterministic",
                            }
                        ],
                        "ai_interpretation": [],
                    },
                    "capability_boundaries": [
                        "Synthetic demo does not claim complete column-level lineage."
                    ],
                }
            ]
        )
