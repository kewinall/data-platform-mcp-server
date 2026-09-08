# Installation / 安裝

## Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

stdio:

```bash
DPMCP_TRANSPORT=stdio data-platform-mcp
```

Streamable HTTP:

```bash
DPMCP_TRANSPORT=streamable-http DPMCP_PORT=8000 data-platform-mcp
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The container runs as UID 10001.

## PostgreSQL

```bash
DPMCP_MODE=postgres DPMCP_POSTGRES_DSN='postgresql://readonly_user:change-me@localhost:5432/analytics' data-platform-mcp
```

## Vertica

```bash
DPMCP_MODE=vertica DPMCP_VERTICA_DSN='vertica://readonly_user:change-me@localhost:5433/warehouse?tlsmode=require' data-platform-mcp
```

## OIDC

See `docs/oidc.md`.

## Kubernetes

```bash
kubectl apply -f examples/kubernetes/namespace-restricted.yaml

helm upgrade --install dpmcp   deploy/helm/data-platform-mcp-server   --namespace data-platform-mcp
```

Production deployments should create a values file defining:

- image repository/tag
- external database DSNs via Secret/ExternalSecret
- OIDC issuer/JWKS/audience
- tenant source policy
- OTLP endpoint
- explicit NetworkPolicy egress

## Release chart

Each v0.4+ GitHub Release publishes a packaged Helm `.tgz` asset after CI and Security succeed.

## Air-gap

See `docs/airgap.md` for the offline wheelhouse/image/Helm bundle workflow.
