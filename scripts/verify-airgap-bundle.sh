#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="${1:-.}"

if [[ ! -f "$BUNDLE_DIR/SHA256SUMS" ]]; then
  echo "SHA256SUMS not found in: $BUNDLE_DIR" >&2
  exit 1
fi

(
  cd "$BUNDLE_DIR"
  sha256sum -c SHA256SUMS
)

echo "Bundle checksum verification succeeded."
