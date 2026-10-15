#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
release="${RELEASE:-26.04}"
arch="${ARCH:-$(uname -m)}"
case "$arch" in
  x86_64) arch=amd64 ;;
  aarch64|arm64) arch=arm64 ;;
esac

echo "Ubuntu Image Factory preflight"
echo "root: $ROOT_DIR"
echo "host: $(uname -s) $(uname -m)"
echo "requested release/arch: $release/$arch"

required=(bash ruby python3 curl sha256sum)
optional=(packer qemu-system-x86_64 qemu-system-aarch64 qemu-img xorriso grub-mkrescue docker syft trivy cosign ansible-lint shellcheck goss)
missing_required=0
for tool in "${required[@]}"; do
  if command -v "$tool" >/dev/null 2>&1; then printf 'OK      %-24s %s\n' "$tool" "$(command -v "$tool")"; else printf 'MISSING %-24s required\n' "$tool"; missing_required=1; fi
done
for tool in "${optional[@]}"; do
  if command -v "$tool" >/dev/null 2>&1; then printf 'OK      %-24s %s\n' "$tool" "$(command -v "$tool")"; else printf 'NOTICE  %-24s optional/target-specific\n' "$tool"; fi
done

if [[ "$release" != "26.04" && "$release" != "24.04" ]]; then
  echo "ERROR: unsupported release $release (choose 26.04 or 24.04)" >&2
  exit 2
fi
if [[ "$arch" != "amd64" && "$arch" != "arm64" ]]; then
  echo "ERROR: unsupported architecture $arch (choose amd64 or arm64)" >&2
  exit 2
fi

free_kb="$(df -Pk "$ROOT_DIR" | awk 'NR==2 {print $4}')"
if [[ -n "$free_kb" && "$free_kb" -lt 20000000 ]]; then
  echo "ERROR: less than 20 GiB free in workspace; VM/ISO builds need more" >&2
  exit 2
fi
if ((missing_required)); then exit 1; fi
echo "preflight complete; target-specific tools may still be required"

