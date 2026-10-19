#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
release="${RELEASE:-26.04}"
arch="${ARCH:-amd64}"
profile="${PROFILE:-minimal}"
output_dir="${OUTPUT_DIR:-$ROOT_DIR/build/iso}"

command -v xorriso >/dev/null 2>&1 || { echo "ERROR: xorriso is required for ISO builds" >&2; exit 1; }
[[ -n "${AUTOINSTALL_PASSWORD_HASH:-}" && -n "${AUTOINSTALL_SSH_PUBLIC_KEY:-}" ]] || { echo "ERROR: AUTOINSTALL_PASSWORD_HASH and AUTOINSTALL_SSH_PUBLIC_KEY are required" >&2; exit 2; }
[[ -n "${AUTOINSTALL_TARGET_DISK_SERIAL:-}" ]] || { echo "ERROR: AUTOINSTALL_TARGET_DISK_SERIAL is mandatory for destructive installer profiles" >&2; exit 2; }

mkdir -p "$output_dir" "$ROOT_DIR/build/autoinstall/$release-$arch"
python3 "$ROOT_DIR/scripts/autoinstall/render.py" --release "$release" --arch "$arch" --profile "$profile" --output "$ROOT_DIR/build/autoinstall/$release-$arch"

iso_version="$([[ "$release" == 26.04 ]] && echo 26.04.1 || echo 24.04.5)"
iso_name="ubuntu-${iso_version}-live-server-${arch}.iso"
if [[ "$arch" == arm64 ]]; then
  iso_base="$([[ "$release" == 26.04 ]] && echo https://cdimage.ubuntu.com/ubuntu/releases/26.04/release || echo https://cdimage.ubuntu.com/ubuntu/releases/24.04/release)"
else
  iso_base="$([[ "$release" == 26.04 ]] && echo https://releases.ubuntu.com/26.04.1 || echo https://releases.ubuntu.com/24.04.5)"
fi
source_iso="$ROOT_DIR/build/iso/$iso_name"
mkdir -p "$ROOT_DIR/build/iso"
if [[ ! -f "$source_iso" ]]; then curl --fail --location --output "$source_iso" "$iso_base/$iso_name"; fi
checksum="$(curl --fail --location --silent --show-error "$iso_base/SHA256SUMS" | awk -v f="$iso_name" '$2 == f || $2 == "*"f {print $1; exit}')"
echo "$checksum  $source_iso" | sha256sum --check -
exec "$ROOT_DIR/scripts/build/build-iso-linux.sh" "$source_iso" "$output_dir/ubuntu-${release}-${arch}-baremetal-${profile}.iso" "$ROOT_DIR/build/autoinstall/$release-$arch"
