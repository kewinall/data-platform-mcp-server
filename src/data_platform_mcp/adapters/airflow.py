import httpx

from data_platform_mcp.models import DagInfo, SearchHit


class AirflowOperationsAdapter:
    """Small Airflow REST adapter.

    This adapter is intentionally conservative in v0.1: it only reads DAG metadata.
    Log aggregation should be connected to a centralized log backend in a later release.
    """

    def __init__(self, base_url: str, token: str | None = None, timeout: float = 10.0):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.client = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout)

    def list_dags(self) -> list[DagInfo]:
        response = self.client.get("/api/v2/dags", params={"limit": 100})
        response.raise_for_status()
        dags = response.json().get("dags", [])
        return [
            DagInfo(dag_id=item["dag_id"], state="unknown", last_run=None)
            for item in dags
            if item.get("dag_id")
        ]

    def get_dag_status(self, dag_id: str) -> DagInfo:
        response = self.client.get(
            f"/api/v2/dags/{dag_id}/dagRuns",
            params={"limit": 1, "order_by": "-logical_date"},
        )
        response.raise_for_status()
        runs = response.json().get("dag_runs", [])
        if not runs:
            return DagInfo(dag_id=dag_id, state="never_run", last_run=None)
        run = runs[0]
        return DagInfo(
            dag_id=dag_id,
            state=run.get("state", "unknown"),
            last_run=run.get("logical_date") or run.get("start_date"),
        )

    def search_logs(self, query: str, limit: int = 10) -> list[SearchHit]:
        raise NotImplementedError(
            "v0.1 does not scrape Airflow task logs. Connect OpenSearch/Loki in a later release."
        )
