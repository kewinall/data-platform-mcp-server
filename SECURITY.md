# Security Policy

Please report vulnerabilities privately through GitHub's security reporting features when available. Do not open a public issue containing credentials, exploit details against a real environment, customer information, or internal infrastructure data.

## Supported release

- `v0.4.x` — supported
- earlier portfolio milestones — upgrade to the latest release before reporting behavior that may already be fixed

## Scope

Security-sensitive components include:

- MCP Streamable HTTP bearer authentication
- OIDC/JWT verification and role mapping
- tenant source authorization
- SQL read-only policy
- PostgreSQL/Vertica read-only adapters
- Airflow/OpenSearch/Loki read-only adapters
- audit and telemetry redaction
- Kubernetes/Helm security configuration
- External Secrets integration
- air-gapped bundle integrity checks

Do not include real bearer tokens, database DSNs, Key Vault identifiers, customer data, or internal hostnames in reports.
