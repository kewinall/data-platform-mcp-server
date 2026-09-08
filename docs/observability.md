# OpenTelemetry Observability

## Signals

v0.4 emits application-level traces and metrics for MCP invocations.

Trace attributes include low-risk operational context such as:

```text
dpmcp.action
dpmcp.required_scope
dpmcp.role
dpmcp.tenant
dpmcp.outcome
```

Metrics:

```text
dpmcp.invocations
dpmcp.invocation.duration
```

Raw SQL, bearer tokens, passwords, and database DSNs are not telemetry attributes.

## OTLP/HTTP

```bash
export DPMCP_OTEL_ENABLED=true
export DPMCP_OTEL_SERVICE_NAME=data-platform-mcp-server
export DPMCP_OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability:4318
export DPMCP_OTEL_METRIC_EXPORT_INTERVAL_MS=60000
```

The server sends:

```text
POST <base>/v1/traces
POST <base>/v1/metrics
```

A minimal Collector example is included at:

```text
examples/otel/collector-config.yaml
```

## Audit correlation

When an OpenTelemetry span has a valid trace ID, the same ID is written into the audit event:

```json
{
  "action": "metadata.get_table",
  "actor": "agent-client",
  "tenant": "tenant-a",
  "role": "analyst",
  "outcome": "success",
  "trace_id": "0123456789abcdef0123456789abcdef"
}
```

This lets an operator move from an audit record to the corresponding distributed trace.

## Production guidance

Prefer exporting OTLP to an OpenTelemetry Collector rather than directly coupling the application to one monitoring vendor. The Collector can then route traces/metrics to Grafana, Tempo, Prometheus, Azure Monitor, Datadog, or another backend.
