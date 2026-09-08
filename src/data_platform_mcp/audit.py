import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any

from data_platform_mcp.auth import Principal

LOGGER = logging.getLogger("data_platform_mcp.audit")


class AuditLogger:
    def __init__(self, enabled: bool = True, path: str | None = None):
        self.enabled = enabled
        self.path = Path(path) if path else None
        self._lock = Lock()

    def record(
        self,
        *,
        action: str,
        principal: Principal,
        outcome: str,
        duration_ms: float,
        metadata: dict[str, Any] | None = None,
        error_type: str | None = None,
    ) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "actor": principal.client_id,
            "subject": principal.subject,
            "role": principal.role,
            "outcome": outcome,
            "duration_ms": round(duration_ms, 3),
            "metadata": metadata or {},
        }
        if error_type:
            event["error_type"] = error_type

        if not self.enabled:
            return event

        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        LOGGER.info(line)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock, self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return event
