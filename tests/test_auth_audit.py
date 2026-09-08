import json

from data_platform_mcp.audit import AuditLogger
from data_platform_mcp.auth import (
    ROLE_SCOPES,
    OidcJwtVerifier,
    Principal,
    StaticTokenVerifier,
)
from data_platform_mcp.tenant import TenantPolicy


async def test_static_token_verifier_assigns_role_scopes_and_tenant() -> None:
    verifier = StaticTokenVerifier.from_json(
        json.dumps(
            {
                "secret-reader-token": {
                    "client_id": "catalog-agent",
                    "role": "reader",
                    "subject": "portfolio-demo",
                    "tenant": "tenant-a",
                }
            }
        ),
        "http://127.0.0.1:8000/mcp",
    )
    token = await verifier.verify_token("secret-reader-token")
    assert token is not None
    assert token.client_id == "catalog-agent"
    assert token.scopes == ROLE_SCOPES["reader"]
    assert token.claims == {"role": "reader", "tenant": "tenant-a"}
    assert await verifier.verify_token("wrong-token") is None


class FakeSigningKey:
    key = "fake-public-key"


class FakeJwkClient:
    def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
        assert token == "signed-jwt"
        return FakeSigningKey()


async def test_oidc_verifier_maps_external_role_and_tenant() -> None:
    def decode_fn(token, key, **kwargs):
        assert token == "signed-jwt"
        assert key == "fake-public-key"
        assert kwargs["audience"] == "api://data-platform-mcp"
        assert kwargs["issuer"] == "https://login.example/tenant/v2.0"
        assert kwargs["algorithms"] == ["RS256"]
        return {
            "sub": "subject-123",
            "exp": 9999999999,
            "azp": "agent-client",
            "roles": ["DataPlatform.Analyst"],
            "tid": "tenant-a",
        }

    verifier = OidcJwtVerifier(
        issuer="https://login.example/tenant/v2.0",
        jwks_url="https://login.example/keys",
        audience="api://data-platform-mcp",
        resource_url="https://mcp.example/mcp",
        algorithms=["RS256"],
        role_claim="roles",
        tenant_claim="tid",
        client_id_claim="azp",
        role_map={"DataPlatform.Analyst": "analyst"},
        jwk_client=FakeJwkClient(),
        decode_fn=decode_fn,
    )
    token = await verifier.verify_token("signed-jwt")
    assert token is not None
    assert token.client_id == "agent-client"
    assert token.scopes == ROLE_SCOPES["analyst"]
    assert token.claims == {"role": "analyst", "tenant": "tenant-a"}


def test_tenant_policy_filters_and_denies_cross_tenant_sources() -> None:
    policy = TenantPolicy.from_json(
        '{"tenant-a":["postgres"],"tenant-b":{"sources":["vertica"]}}',
        enabled=True,
    )
    principal = Principal(
        client_id="catalog-agent",
        role="analyst",
        subject="subject-123",
        tenant="tenant-a",
        scopes=tuple(ROLE_SCOPES["analyst"]),
    )
    assert policy.filter_sources(principal, ["postgres", "vertica"]) == ["postgres"]
    policy.require_source(principal, "postgres")

    try:
        policy.require_source(principal, "vertica")
    except PermissionError as exc:
        assert "tenant-a" in str(exc)
    else:
        raise AssertionError("cross-tenant source access should be denied")


def test_audit_jsonl_contains_tenant_trace_but_not_credentials(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLogger(enabled=True, path=str(path))
    principal = Principal(
        client_id="catalog-agent",
        role="reader",
        subject="portfolio-demo",
        tenant="tenant-a",
        scopes=("platform:read", "catalog:read"),
    )
    audit.record(
        action="sql.explain",
        principal=principal,
        outcome="success",
        duration_ms=1.23,
        metadata={"sql_fingerprint": "abc123"},
        trace_id="0123456789abcdef",
    )
    payload = path.read_text(encoding="utf-8")
    assert "catalog-agent" in payload
    assert "tenant-a" in payload
    assert "0123456789abcdef" in payload
    assert "abc123" in payload
    assert "secret-reader-token" not in payload
