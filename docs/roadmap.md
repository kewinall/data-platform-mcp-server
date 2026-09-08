# Roadmap / 開發路線

## v0.1 — Foundation ✅
- MCP Python SDK v2
- stdio / Streamable HTTP
- Demo catalog + DataOps tools
- PostgreSQL read-only catalog adapter
- CI / security scan

## v0.2 — DataOps Integration ✅
- Airflow 3 public REST API read-only adapter
- OpenSearch ETL log search
- Grafana Loki ETL log search
- MCP resources and prompts
- Protocol-level MCP integration tests

## v0.3 — Enterprise Data Platform ✅
- Vertica catalog adapter
- PostgreSQL + Vertica composite catalog
- Metadata / lineage
- SQLGlot AST read-only SQL policy
- Bearer RBAC
- Structured audit JSONL
- CI/Security-gated release automation

## v0.4 — Production Delivery ✅
- Kubernetes + Helm
- OIDC/JWKS resource-server authentication
- Keycloak and Microsoft Entra ID configuration examples
- Multi-tenancy and tenant-aware source authorization
- OpenTelemetry traces + metrics via OTLP/HTTP
- External Secrets Operator integration
- Azure Key Vault Workload Identity example
- Restricted Pod Security defaults
- NetworkPolicy / PDB / HPA
- Air-gapped deployment bundle
- Helm chart release asset

## Next ideas / 後續可延伸
- Database-level row/column policy integration
- OPA / Cedar authorization policy backend
- Catalog integrations such as OpenMetadata/DataHub
- Kubernetes Gateway API / Ingress examples
- Signed OCI images and SBOM/provenance
- GitOps examples for Argo CD / Flux
