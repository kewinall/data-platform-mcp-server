import json

import httpx

from data_platform_mcp.adapters.airflow import AirflowOperationsAdapter
from data_platform_mcp.adapters.composite import CompositeCatalogAdapter
from data_platform_mcp.adapters.demo import DemoCatalogAdapter
from data_platform_mcp.adapters.logs import LokiLogAdapter, OpenSearchLogAdapter


def test_airflow_lists_dags_and_latest_run() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/dags":
            return httpx.Response(
                200,
                json={"dags": [{"dag_id": "sales_daily", "is_paused": False}]},
            )
        if request.url.path == "/api/v2/dags/sales_daily/dagRuns":
            return httpx.Response(
                200,
                json={
                    "dag_runs": [
                        {"state": "failed", "logical_date": "2026-09-07T01:00:00Z"},
                        {"state": "success", "logical_date": "2026-09-08T01:00:00Z"},
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://airflow.example",
    )
    adapter = AirflowOperationsAdapter("https://airflow.example", client=client)

    assert adapter.list_dags()[0].dag_id == "sales_daily"
    status = adapter.get_dag_status("sales_daily")
    assert status.state == "success"
    assert status.last_run == "2026-09-08T01:00:00Z"


def test_opensearch_log_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["size"] == 5
        return httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_index": "etl-logs-2026.09.08",
                            "_source": {
                                "@timestamp": "2026-09-08T14:15:00Z",
                                "level": "ERROR",
                                "dag_id": "quality_checks",
                                "task_id": "validate_orders",
                                "message": "Row-count guardrail failed",
                            },
                        }
                    ]
                }
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://opensearch.example",
    )
    adapter = OpenSearchLogAdapter(
        "https://opensearch.example",
        "etl-logs-*",
        client=client,
    )

    hits = adapter.search("guardrail", 5)
    assert hits[0].source == "opensearch"
    assert "quality_checks" in hits[0].title


def test_loki_log_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/loki/api/v1/query_range"
        assert "failed" in request.url.params["query"]
        return httpx.Response(
            200,
            json={
                "data": {
                    "result": [
                        {
                            "stream": {"job": "airflow", "dag_id": "quality_checks"},
                            "values": [["1", "validation failed"]],
                        }
                    ]
                }
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://loki.example",
    )
    adapter = LokiLogAdapter(
        "https://loki.example",
        '{job="airflow"} |= "{query}"',
        client=client,
    )

    hits = adapter.search("failed", 10)
    assert hits[0].source == "loki"
    assert hits[0].snippet == "validation failed"


def test_composite_catalog_routes_by_source() -> None:
    composite = CompositeCatalogAdapter([DemoCatalogAdapter()])
    assert composite.list_sources() == ["analytics"]
    assert "orders" in composite.list_tables("analytics", "public")
