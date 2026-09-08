import httpx

from data_platform_mcp.models import DagInfo


class AirflowOperationsAdapter:
    """Read-only adapter for the stable Airflow 3 public REST API (/api/v2)."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

    def list_dags(self) -> list[DagInfo]:
        response = self.client.get("/api/v2/dags", params={"limit": 100})
        response.raise_for_status()
        dags = response.json().get("dags", [])
        return [
            DagInfo(
                dag_id=item["dag_id"],
                state="paused" if item.get("is_paused") else "active",
                last_run=None,
            )
            for item in dags
            if item.get("dag_id")
        ]

    def get_dag_status(self, dag_id: str) -> DagInfo:
        response = self.client.get(f"/api/v2/dags/{dag_id}/dagRuns", params={"limit": 100})
        response.raise_for_status()
        runs = response.json().get("dag_runs", [])
        if not runs:
            return DagInfo(dag_id=dag_id, state="never_run", last_run=None)

        def run_time(item: dict) -> str:
            return item.get("logical_date") or item.get("start_date") or ""

        latest = max(runs, key=run_time)
        return DagInfo(
            dag_id=dag_id,
            state=latest.get("state", "unknown"),
            last_run=run_time(latest) or None,
        )
