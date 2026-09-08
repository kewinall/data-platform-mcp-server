import re
from typing import Any

import httpx

from data_platform_mcp.models import SearchHit


def _safe_loki_query(template: str, query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return template.replace("{query}", escaped)


class OpenSearchLogAdapter:
    """Read-only OpenSearch log search adapter."""

    def __init__(
        self,
        base_url: str,
        index: str,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        client: httpx.Client | None = None,
    ):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        auth = (username, password) if username and password else None
        self.index = index
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            auth=auth,
            timeout=10.0,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        body = {
            "size": limit,
            "sort": [{"@timestamp": {"order": "desc", "unmapped_type": "date"}}],
            "query": {
                "simple_query_string": {
                    "query": query,
                    "fields": ["message^3", "dag_id", "task_id", "job", "level"],
                    "default_operator": "and",
                }
            },
        }
        response = self.client.post(f"/{self.index}/_search", json=body)
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
        return [self._to_hit(item) for item in hits]

    @staticmethod
    def _to_hit(item: dict[str, Any]) -> SearchHit:
        source = item.get("_source", {})
        title_parts = [
            str(source.get(key))
            for key in ("dag_id", "task_id", "job")
            if source.get(key) is not None
        ]
        return SearchHit(
            source="opensearch",
            title=" / ".join(title_parts) or str(item.get("_index", "etl-log")),
            snippet=str(source.get("message") or source.get("log") or ""),
            metadata={
                "timestamp": source.get("@timestamp") or source.get("timestamp"),
                "level": source.get("level"),
                "index": item.get("_index"),
            },
        )


class LokiLogAdapter:
    """Read-only Grafana Loki query_range adapter."""

    def __init__(
        self,
        base_url: str,
        query_template: str,
        token: str | None = None,
        client: httpx.Client | None = None,
    ):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.query_template = query_template
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=10.0,
        )

    def search(self, query: str, limit: int = 10) -> list[SearchHit]:
        logql = _safe_loki_query(self.query_template, query)
        response = self.client.get(
            "/loki/api/v1/query_range",
            params={"query": logql, "limit": limit, "direction": "backward"},
        )
        response.raise_for_status()
        streams = response.json().get("data", {}).get("result", [])
        hits: list[SearchHit] = []
        for stream in streams:
            labels = stream.get("stream", {})
            for timestamp, line in stream.get("values", []):
                hits.append(
                    SearchHit(
                        source="loki",
                        title=self._title(labels),
                        snippet=str(line),
                        metadata={"timestamp_ns": timestamp, "labels": labels},
                    )
                )
                if len(hits) >= limit:
                    return hits
        return hits

    @staticmethod
    def _title(labels: dict[str, Any]) -> str:
        preferred = [
            str(labels[key])
            for key in ("dag_id", "task_id", "job", "app")
            if labels.get(key)
        ]
        if preferred:
            return " / ".join(preferred)
        return ", ".join(f"{key}={value}" for key, value in sorted(labels.items())) or "log"

    @staticmethod
    def redact_query(logql: str) -> str:
        return re.sub(r'(?i)(password|token|secret)="[^"]+"', r'\1="***"', logql)
