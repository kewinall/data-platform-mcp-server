import json
from dataclasses import dataclass

from data_platform_mcp.auth import Principal


@dataclass(frozen=True)
class TenantRule:
    sources: frozenset[str]


class TenantPolicy:
    def __init__(self, *, enabled: bool, rules: dict[str, TenantRule] | None = None):
        self.enabled = enabled
        self.rules = rules or {}

    @classmethod
    def from_json(cls, raw: str | None, *, enabled: bool) -> "TenantPolicy":
        if not enabled:
            return cls(enabled=False)

        if not raw:
            raise ValueError(
                "DPMCP_TENANT_ALLOWED_SOURCES_JSON is required when multi-tenancy is enabled"
            )
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("DPMCP_TENANT_ALLOWED_SOURCES_JSON must be valid JSON") from exc
        if not isinstance(payload, dict) or not payload:
            raise ValueError("Tenant policy must define at least one tenant")

        rules: dict[str, TenantRule] = {}
        for tenant, value in payload.items():
            if isinstance(value, list):
                sources = value
            elif isinstance(value, dict):
                sources = value.get("sources", [])
            else:
                raise ValueError(f"Tenant rule for {tenant!r} must be a list or object")
            if not all(isinstance(source, str) and source for source in sources):
                raise ValueError(f"Tenant rule for {tenant!r} contains an invalid source")
            rules[str(tenant)] = TenantRule(sources=frozenset(sources))
        return cls(enabled=True, rules=rules)

    def _rule(self, principal: Principal) -> TenantRule:
        if principal.role == "local":
            return TenantRule(sources=frozenset({"*"}))
        if not principal.tenant:
            raise PermissionError("Authenticated caller has no tenant claim")
        try:
            return self.rules[principal.tenant]
        except KeyError as exc:
            raise PermissionError(f"Tenant is not configured: {principal.tenant}") from exc

    def filter_sources(self, principal: Principal, sources: list[str]) -> list[str]:
        if not self.enabled:
            return sources
        allowed = self._rule(principal).sources
        if "*" in allowed:
            return sources
        return [source for source in sources if source in allowed]

    def require_source(self, principal: Principal, source: str) -> None:
        if not self.enabled:
            return
        allowed = self._rule(principal).sources
        if "*" not in allowed and source not in allowed:
            raise PermissionError(
                f"Tenant {principal.tenant!r} is not allowed to access source {source!r}"
            )
