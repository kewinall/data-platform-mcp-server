# Kubernetes / Helm Deployment

## 繁體中文

v0.4 提供正式 Helm Chart：

```text
deploy/helm/data-platform-mcp-server
```

預設安全設定包括：

- non-root UID/GID `10001`
- `readOnlyRootFilesystem: true`
- `allowPrivilegeEscalation: false`
- Linux capabilities 全部 drop
- `seccompProfile: RuntimeDefault`
- 不自動掛載 Kubernetes ServiceAccount token
- CPU / memory requests + limits
- readiness / liveness TCP probes
- PodDisruptionBudget
- NetworkPolicy
- optional HPA
- optional ExternalSecret

### 安裝

```bash
kubectl apply -f examples/kubernetes/namespace-restricted.yaml

helm upgrade --install dpmcp \
  deploy/helm/data-platform-mcp-server \
  --namespace data-platform-mcp
```

本機測試：

```bash
kubectl -n data-platform-mcp port-forward svc/dpmcp-data-platform-mcp-server 8000:8000
```

MCP endpoint：

```text
http://127.0.0.1:8000/mcp
```

## NetworkPolicy

預設：

```text
Ingress:
  same namespace -> TCP/8000

Egress:
  DNS only
```

因此若啟用 PostgreSQL、Vertica、OIDC、Airflow、OpenSearch、Loki 或 OTLP Collector，需要在 values 中明確加入 egress。

範例：

```yaml
networkPolicy:
  egress:
    additionalRules:
      - to:
          - ipBlock:
              cidr: 10.20.0.10/32
        ports:
          - protocol: TCP
            port: 5433
```

## Secret injection

若已有 Kubernetes Secret：

```yaml
existingSecret: data-platform-mcp-secrets
```

若使用 External Secrets Operator：

```yaml
externalSecret:
  enabled: true
  secretStoreRef:
    name: azure-key-vault
    kind: SecretStore
  data:
    - secretKey: DPMCP_VERTICA_DSN
      remoteRef:
        key: data-platform/vertica-dsn
```

應用 Pod 不需要直接存取 Key Vault；External Secrets Operator 負責同步成 Kubernetes Secret。

## English

The chart is designed around explicit least privilege. It runs non-root, uses a read-only root filesystem, disables ServiceAccount token automounting, and starts with restrictive network egress. Production deployments should define only the database, identity-provider, logging, orchestration, and telemetry destinations that each environment actually requires.
