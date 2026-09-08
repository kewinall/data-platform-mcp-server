from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span


class Telemetry:
    def __init__(
        self,
        *,
        enabled: bool,
        service_name: str,
        service_version: str,
        environment: str,
        endpoint: str | None = None,
        metric_export_interval_ms: int = 60000,
    ):
        self.enabled = enabled

        if enabled:
            if not endpoint:
                raise ValueError(
                    "DPMCP_OTEL_EXPORTER_OTLP_ENDPOINT is required when telemetry is enabled"
                )
            resource = Resource.create(
                {
                    SERVICE_NAME: service_name,
                    SERVICE_VERSION: service_version,
                    "deployment.environment.name": environment,
                }
            )
            base = endpoint.rstrip("/")

            tracer_provider = TracerProvider(resource=resource)
            tracer_provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
            )
            self.tracer = tracer_provider.get_tracer(service_name)

            reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=f"{base}/v1/metrics"),
                export_interval_millis=metric_export_interval_ms,
            )
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
            self.meter = meter_provider.get_meter(service_name)
        else:
            self.tracer = trace.get_tracer(service_name)
            self.meter = metrics.get_meter(service_name)

        self.invocations = self.meter.create_counter(
            "dpmcp.invocations",
            unit="1",
            description="MCP tool/resource/prompt invocations",
        )
        self.duration = self.meter.create_histogram(
            "dpmcp.invocation.duration",
            unit="ms",
            description="MCP invocation duration",
        )

    @contextmanager
    def span(self, action: str, scope: str) -> Iterator[Span]:
        with self.tracer.start_as_current_span(
            f"dpmcp.{action}",
            attributes={"dpmcp.action": action, "dpmcp.required_scope": scope},
        ) as span:
            yield span

    @staticmethod
    def set_identity(span: Span, *, role: str, tenant: str | None) -> None:
        span.set_attribute("dpmcp.role", role)
        if tenant:
            span.set_attribute("dpmcp.tenant", tenant)

    @staticmethod
    def trace_id(span: Span) -> str | None:
        context = span.get_span_context()
        if not context.is_valid:
            return None
        return f"{context.trace_id:032x}"

    def record(self, *, action: str, outcome: str, role: str, duration_ms: float) -> None:
        attributes: dict[str, Any] = {
            "dpmcp.action": action,
            "dpmcp.outcome": outcome,
            "dpmcp.role": role,
        }
        self.invocations.add(1, attributes)
        self.duration.record(duration_ms, attributes)
