import json
from dataclasses import dataclass
from typing import Literal

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from pydantic import BaseModel

Role = Literal["reader", "analyst", "operator", "admin"]

ROLE_SCOPES: dict[Role, list[str]] = {
    "reader": ["platform:read", "catalog:read", "runbook:read"],
    "analyst": [
        "platform:read",
        "catalog:read",
        "runbook:read",
        "sql:explain",
        "lineage:read",
    ],
    "operator": [
        "platform:read",
        "catalog:read",
        "runbook:read",
        "sql:explain",
        "lineage:read",
        "operations:read",
        "logs:read",
    ],
    "admin": [
        "platform:read",
        "catalog:read",
        "runbook:read",
        "sql:explain",
        "lineage:read",
        "operations:read",
        "logs:read",
        "audit:read",
    ],
}


class TokenConfig(BaseModel):
    client_id: str
    role: Role
    subject: str | None = None


@dataclass(frozen=True)
class Principal:
    client_id: str
    role: str
    subject: str | None
    scopes: tuple[str, ...]


class StaticTokenVerifier(TokenVerifier):
    def __init__(self, token_map: dict[str, TokenConfig], resource_url: str):
        self.token_map = token_map
        self.resource_url = resource_url

    @classmethod
    def from_json(cls, raw: str, resource_url: str) -> "StaticTokenVerifier":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("DPMCP_API_TOKENS_JSON must be valid JSON") from exc
        if not isinstance(payload, dict) or not payload:
            raise ValueError("DPMCP_API_TOKENS_JSON must define at least one token")
        token_map = {token: TokenConfig.model_validate(config) for token, config in payload.items()}
        return cls(token_map, resource_url)

    async def verify_token(self, token: str) -> AccessToken | None:
        config = self.token_map.get(token)
        if config is None:
            return None
        return AccessToken(
            token=token,
            client_id=config.client_id,
            scopes=ROLE_SCOPES[config.role],
            resource=self.resource_url,
            subject=config.subject or config.client_id,
            claims={"role": config.role},
        )


def current_principal() -> Principal:
    token = get_access_token()
    if token is None:
        return Principal(
            client_id="local-process",
            role="local",
            subject=None,
            scopes=("local:trusted",),
        )
    claims = token.claims or {}
    return Principal(
        client_id=token.client_id,
        role=str(claims.get("role", "custom")),
        subject=token.subject,
        scopes=tuple(token.scopes),
    )


def require_scope(scope: str) -> Principal:
    token = get_access_token()
    principal = current_principal()
    if token is None:
        return principal
    if scope not in token.scopes:
        raise PermissionError(f"Caller lacks required scope: {scope}")
    return principal
