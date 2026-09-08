#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(
  python - <<'PY'
import tomllib

with open("pyproject.toml", "rb") as handle:
    print(tomllib.load(handle)["project"]["version"])
PY
)"

IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-data-platform-mcp-server}"
OUTPUT_ROOT="${OUTPUT_ROOT:-dist}"
BUNDLE_DIR="${OUTPUT_ROOT}/data-platform-mcp-server-${VERSION}-airgap"
ARCHIVE="${OUTPUT_ROOT}/data-platform-mcp-server-${VERSION}-airgap.tar.gz"

for command in python docker helm sha256sum tar; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "Required command not found: $command" >&2
    exit 1
  }
done

rm -rf "$BUNDLE_DIR" "$ARCHIVE"
mkdir -p "$BUNDLE_DIR/wheelhouse" "$BUNDLE_DIR/images" "$BUNDLE_DIR/helm"

echo "[1/5] Building Python wheelhouse"
python -m pip wheel --wheel-dir "$BUNDLE_DIR/wheelhouse" .

echo "[2/5] Building application container image"
docker build --pull=false -t "${IMAGE_REPOSITORY}:${VERSION}" .

echo "[3/5] Exporting OCI image"
docker save "${IMAGE_REPOSITORY}:${VERSION}"   -o "$BUNDLE_DIR/images/data-platform-mcp-server-${VERSION}.tar"

echo "[4/5] Packaging Helm chart and deployment material"
helm package deploy/helm/data-platform-mcp-server --destination "$BUNDLE_DIR/helm"
cp .env.example README.md LICENSE "$BUNDLE_DIR/"
cp -R docs "$BUNDLE_DIR/docs"
cp scripts/verify-airgap-bundle.sh "$BUNDLE_DIR/"

echo "[5/5] Generating checksums and archive"
(
  cd "$BUNDLE_DIR"
  find . -type f ! -name SHA256SUMS -print0     | sort -z     | xargs -0 sha256sum > SHA256SUMS
)
tar -C "$OUTPUT_ROOT" -czf "$ARCHIVE" "$(basename "$BUNDLE_DIR")"

echo "Air-gapped bundle created:"
echo "  $ARCHIVE"
