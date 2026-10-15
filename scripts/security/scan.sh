#!/usr/bin/env bash
set -Eeuo pipefail

target="${ARTIFACT:-build/container}"
out_dir="${SECURITY_OUTPUT_DIR:-artifacts/security}"
mkdir -p "$out_dir"
command -v trivy >/dev/null 2>&1 || { echo "ERROR: trivy is required; refusing to produce an empty vulnerability report" >&2; exit 1; }
command -v syft >/dev/null 2>&1 || { echo "ERROR: syft is required; refusing to produce an empty SBOM" >&2; exit 1; }

if [[ "$target" == build/container || "$target" == docker://* || "$target" == *:* ]]; then
  image="${IMAGE_TAG:-ubuntu-image-factory:26.04-amd64}"
  syft "$image" -o spdx-json > "$out_dir/sbom.spdx.json"
  trivy image --scanners vuln,secret,misconfig --format json --output "$out_dir/trivy.json" --exit-code 1 "$image"
else
  syft "dir:$target" -o spdx-json > "$out_dir/sbom.spdx.json"
  trivy fs --scanners vuln,secret,misconfig --format json --output "$out_dir/trivy.json" --exit-code 1 "$target"
fi
echo "security scan complete; reports are in $out_dir"

