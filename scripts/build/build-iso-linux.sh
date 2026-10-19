#!/usr/bin/env bash
set -Eeuo pipefail

source_iso="${1:?source ISO required}"
output_iso="${2:?output ISO required}"
seed_dir="${3:?seed directory required}"
command -v xorriso >/dev/null 2>&1 || { echo "ERROR: xorriso is required" >&2; exit 1; }
[[ "$(uname -s)" == Linux ]] || { echo "ERROR: production ISO assembly requires Linux; use a Linux runner" >&2; exit 1; }

xorriso -indev "$source_iso" -outdev "$output_iso" \
  -map "$seed_dir/user-data" /server/user-data \
  -map "$seed_dir/meta-data" /server/meta-data \
  -boot_image any replay -commit >/dev/null
sha256sum "$output_iso" > "$output_iso.sha256"
echo "built $output_iso"
