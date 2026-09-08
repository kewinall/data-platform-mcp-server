import json

from data_platform_mcp.audit import AuditLogger
from data_platform_mcp.auth import ROLE_SCOPES, Principal, StaticTokenVerifier


async def test_static_token_verifier_assigns_role_scopes() -> None:
    verifier = StaticTokenVerifier.from_json(
        json.dumps(
            {
                "secret-reader-token": {
                    "client_id": "catalog-agent",
                    "role": "reader",
                    "subject": "portfolio-demo",
                }
            }
        ),
        "http://127.0.0.1:8000/mcp",
    )
    token = await verifier.verify_token("secret-reader-token")
    assert token is not None
    assert token.client_id == "catalog-agent"
    assert token.scopes == ROLE_SCOPES["reader"]
    assert token.claims == {"role": "reader"}
    assert await verifier.verify_token("wrong-token") is None


def test_audit_jsonl_contains_actor_but_not_credentials(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLogger(enabled=True, path=str(path))
    principal = Principal(
        client_id="catalog-agent",
        role="reader",
        subject="portfolio-demo",
        scopes=("platform:read", "catalog:read"),
    )
    audit.record(
        action="sql.explain",
        principal=principal,
        outcome="success",
        duration_ms=1.23,
        metadata={"sql_fingerprint": "abc123"},
    )
    payload = path.read_text(encoding="utf-8")
    assert "catalog-agent" in payload
    assert "abc123" in payload
    assert "secret-reader-token" not in payload
