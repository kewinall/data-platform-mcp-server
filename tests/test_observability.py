import pytest

from data_platform_mcp.observability import Telemetry


def test_disabled_telemetry_is_noop_safe() -> None:
    telemetry = Telemetry(
        enabled=False,
        service_name="test-service",
        service_version="0.4.0",
        environment="test",
    )
    with telemetry.span("catalog.list_sources", "catalog:read") as span:
        telemetry.set_identity(span, role="reader", tenant="tenant-a")
        telemetry.record(
            action="catalog.list_sources",
            outcome="success",
            role="reader",
            duration_ms=2.5,
        )
        assert telemetry.trace_id(span) is None


def test_enabled_telemetry_requires_otlp_endpoint() -> None:
    with pytest.raises(ValueError, match="OTLP_ENDPOINT"):
        Telemetry(
            enabled=True,
            service_name="test-service",
            service_version="0.4.0",
            environment="test",
        )
