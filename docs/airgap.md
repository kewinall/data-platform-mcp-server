# Offline / Air-gapped Deployment

## Goal

The target network should not need PyPI, Docker Hub, GitHub, or other public package repositories during installation.

## Build on an internet-connected staging workstation

Requirements:

```text
Python
Docker
Helm
sha256sum
tar
```

Build:

```bash
make airgap
```

or:

```bash
bash scripts/build-airgap-bundle.sh
```

Output:

```text
dist/data-platform-mcp-server-0.4.0-airgap.tar.gz
```

The bundle contains:

```text
wheelhouse/       Python project + dependency wheels
images/           docker save image tar
helm/             packaged Helm chart
docs/
.env.example
README.md
LICENSE
SHA256SUMS
verify-airgap-bundle.sh
```

## Transfer

Move the archive through the organization's approved transfer mechanism. After transfer:

```bash
tar -xzf data-platform-mcp-server-0.4.0-airgap.tar.gz
cd data-platform-mcp-server-0.4.0-airgap
bash verify-airgap-bundle.sh .
```

Do not deploy if checksum validation fails.

## Load container image

```bash
docker load -i images/data-platform-mcp-server-0.4.0.tar
```

For Kubernetes, retag and push the image to the organization's internal registry.

## Offline Python installation

```bash
python -m pip install \
  --no-index \
  --find-links wheelhouse \
  data-platform-mcp-server==0.4.0
```

## Offline Helm

```bash
helm upgrade --install dpmcp \
  helm/data-platform-mcp-server-0.4.0.tgz \
  --namespace data-platform-mcp
```

The Helm chart itself has no external chart dependencies.
