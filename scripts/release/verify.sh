#!/usr/bin/env bash
set -Eeuo pipefail

manifest="${MANIFEST:-artifacts/release/manifest.json}"
[[ -f "$manifest" ]] || { echo "ERROR: manifest not found: $manifest" >&2; exit 1; }
python3 - "$manifest" <<'PY'
import hashlib, json, pathlib, sys
manifest = pathlib.Path(sys.argv[1])
data = json.loads(manifest.read_text())
for item in data.get("artifacts", []):
    path = pathlib.Path(item["path"])
    expected = item["sha256"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"checksum mismatch: {path}")
    print(f"verified {path} {digest}")
PY
if [[ "${VERIFY_SIGNATURES:-0}" == 1 ]]; then
  command -v cosign >/dev/null 2>&1 || { echo "ERROR: cosign required for signature verification" >&2; exit 1; }
  echo "Cosign verification must be supplied with the release identity and issuer in COSIGN_CERT_IDENTITY/COSIGN_CERT_ISSUER."
fi
echo "release verification complete"

