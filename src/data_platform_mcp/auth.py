import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

import jwt
from jwt import PyJWKClient
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
    tenant: str | None = None


@dataclass(frozen=True)
class Principal:
    client_id: str
    role: str
    subject: str | None
    tenant: str | None
    scopes: tuple[str, ...]


def _claim_value(claims: dict[str, Any], path: str) -> Any:
    current: Any = claims
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _parse_role_map(raw: str | None) -> dict[str, Role]:
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DPMCP_OIDC_ROLE_MAP_JSON must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("DPMCP_OIDC_ROLE_MAP_JSON must be a JSON object")

    result: dict[str, Role] = {}
    for external, internal in payload.items():
        if internal not in ROLE_SCOPES:
            raise ValueError(f"Unsupported internal role in OIDC role map: {internal!r}")
        result[str(external)] = cast(Role, internal)
    return result


def _resolve_role(
    claims: dict[str, Any],
    *,
    claim_path: str,
    role_map: dict[str, Role],
) -> Role | None:
    value = _claim_value(claims, claim_path)
    candidates: list[str]
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, list):
        candidates = [str(item) for item in value]
    else:
        return None

    for candidate in candidates:
        mapped = role_map.get(candidate, candidate)
        if mapped in ROLE_SCOPES:
            return cast(Role, mapped)
    return None


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
        token_map = {
            token: TokenConfig.model_validate(config)
            for token, config in payload.items()
        }
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
            claims={"role": config.role, "tenant": config.tenant},
        )


class OidcJwtVerifier(TokenVerifier):
    def __init__(
        self,
        *,
        issuer: str,
        jwks_url: str,
        audience: str,
        resource_url: str,
        algorithms: list[str],
        role_claim: str,
        tenant_claim: str,
        client_id_claim: str,
        role_map: dict[str, Role] | None = None,
        jwk_client: Any | None = None,
        decode_fn: Callable[..., dict[str, Any]] | None = None,
    ):
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.resource_url = resource_url
        self.algorithms = algorithms
        self.role_claim = role_claim
        self.tenant_claim = tenant_claim
        self.client_id_claim = client_id_claim
        self.role_map = role_map or {}
        self.jwk_client = jwk_client or PyJWKClient(jwks_url)
        self.decode_fn = decode_fn or jwt.decode

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            signing_key = self.jwk_client.get_signing_key_from_jwt(token).key
            claims = self.decode_fn(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "sub"]},
            )
        except Exception:
            return None

        role = _resolve_role(
            claims,
            claim_path=self.role_claim,
            role_map=self.role_map,
        )
        if role is None:
            return None

        subject = str(claims["sub"])
        client_id = _claim_value(claims, self.client_id_claim)
        if not client_id:
            client_id = claims.get("azp") or claims.get("client_id") or subject

        tenant_value = _claim_value(claims, self.tenant_claim)
        tenant = str(tenant_value) if tenant_value is not None else None

        return AccessToken(
            token=token,
            client_id=str(client_id),
            scopes=ROLE_SCOPES[role],
            resource=self.resource_url,
            subject=subject,
            claims={"role": role, "tenant": tenant},
        )


def build_token_verifier(
    *,
    auth_mode: str,
    resource_url: str,
    api_tokens_json: str | None,
    issuer: str,
    oidc_jwks_url: str | None,
    oidc_audience: str | None,
    oidc_algorithms: str,
    oidc_role_claim: str,
    oidc_tenant_claim: str,
    oidc_client_id_claim: str,
    oidc_role_map_json: str | None,
) -> TokenVerifier:
    if auth_mode == "static":
        if not api_tokens_json:
            raise ValueError(
                "DPMCP_API_TOKENS_JSON is required when DPMCP_AUTH_MODE=static"
            )
        return StaticTokenVerifier.from_json(api_tokens_json, resource_url)

    if auth_mode == "oidc":
        if not oidc_jwks_url:
            raise ValueError("DPMCP_OIDC_JWKS_URL is required when DPMCP_AUTH_MODE=oidc")
        if not oidc_audience:
            raise ValueError("DPMCP_OIDC_AUDIENCE is required when DPMCP_AUTH_MODE=oidc")
        algorithms = [item.strip() for item in oidc_algorithms.split(",") if item.strip()]
        if not algorithms:
            raise ValueError("DPMCP_OIDC_ALGORITHMS must contain at least one algorithm")
        return OidcJwtVerifier(
            issuer=issuer,
            jwks_url=oidc_jwks_url,
            audience=oidc_audience,
            resource_url=resource_url,
            algorithms=algorithms,
            role_claim=oidc_role_claim,
            tenant_claim=oidc_tenant_claim,
            client_id_claim=oidc_client_id_claim,
            role_map=_parse_role_map(oidc_role_map_json),
        )

    raise ValueError(f"Unsupported authentication mode: {auth_mode}")


def current_principal() -> Principal:
    token = get_access_token()
    if token is None:
        return Principal(
            client_id="local-process",
            role="local",
            subject=None,
            tenant="local",
            scopes=("local:trusted",),
        )
    claims = token.claims or {}
    tenant = claims.get("tenant")
    return Principal(
        client_id=token.client_id,
        role=str(claims.get("role", "custom")),
        subject=token.subject,
        tenant=str(tenant) if tenant is not None else None,
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
