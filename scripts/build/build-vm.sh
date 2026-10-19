#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
release="${RELEASE:-26.04}"
arch="${ARCH:-amd64}"
format="${FORMAT:-qcow2}"
profile="${PROFILE:-hardened}"
output_dir="${OUTPUT_DIR:-$ROOT_DIR/build/vm}"

case "$format" in qcow2|raw) ;; *) echo "ERROR: FORMAT must be qcow2 or raw" >&2; exit 2 ;; esac
[[ "$arch" == amd64 || "$arch" == arm64 ]] || { echo "ERROR: unsupported ARCH=$arch" >&2; exit 2; }
[[ "$release" == 26.04 || "$release" == 24.04 ]] || { echo "ERROR: unsupported RELEASE=$release" >&2; exit 2; }
command -v packer >/dev/null 2>&1 || { echo "ERROR: packer is required for VM builds" >&2; exit 1; }
command -v qemu-img >/dev/null 2>&1 || { echo "ERROR: qemu-img is required for VM builds" >&2; exit 1; }

mkdir -p "$output_dir" "$ROOT_DIR/build/autoinstall/$release-$arch"
if [[ -z "${AUTOINSTALL_PASSWORD_HASH:-}" || -z "${AUTOINSTALL_SSH_PUBLIC_KEY:-}" || -z "${AUTOINSTALL_SSH_PRIVATE_KEY_FILE:-}" ]]; then
  echo "ERROR: AUTOINSTALL_PASSWORD_HASH, AUTOINSTALL_SSH_PUBLIC_KEY, and AUTOINSTALL_SSH_PRIVATE_KEY_FILE are required; no credentials are generated or embedded automatically" >&2
  exit 2
fi
[[ -f "$AUTOINSTALL_SSH_PRIVATE_KEY_FILE" ]] || { echo "ERROR: private key file not found: $AUTOINSTALL_SSH_PRIVATE_KEY_FILE" >&2; exit 2; }
export AUTOINSTALL_TARGET_DISK_SERIAL="${AUTOINSTALL_TARGET_DISK_SERIAL:-FACTORY-QEMU-DISK}"
python3 "$ROOT_DIR/scripts/autoinstall/render.py" --release "$release" --arch "$arch" --profile "$profile" --output "$ROOT_DIR/build/autoinstall/$release-$arch"

iso_version="$([[ "$release" == 26.04 ]] && echo 26.04.1 || echo 24.04.5)"
if [[ "$arch" == arm64 ]]; then
  iso_base="$([[ "$release" == 26.04 ]] && echo https://cdimage.ubuntu.com/ubuntu/releases/26.04/release || echo https://cdimage.ubuntu.com/ubuntu/releases/24.04/release)"
else
  iso_base="$([[ "$release" == 26.04 ]] && echo https://releases.ubuntu.com/26.04.1 || echo https://releases.ubuntu.com/24.04.5)"
fi
iso_name="ubuntu-${iso_version}-live-server-${arch}.iso"
checksum_url="$iso_base/SHA256SUMS"
checksum="$(curl --fail --location --silent --show-error "$checksum_url" | awk -v f="$iso_name" '$2 == f || $2 == "*"f {print $1; exit}')"
[[ "$checksum" =~ ^[a-fA-F0-9]{64}$ ]] || { echo "ERROR: could not resolve trusted checksum for $iso_name from $checksum_url" >&2; exit 1; }

cd "$ROOT_DIR/packer"
packer init -upgrade=false .
packer build -color=false \
  -var "release=$release" -var "architecture=$arch" \
  -var "iso_url=$iso_base/$iso_name" -var "iso_checksum=sha256:$checksum" \
  -var "output_directory=$output_dir" -var "desired_format=$format" \
  -var "accelerator=$( [[ -e /dev/kvm ]] && echo kvm || echo none )" \
  -var "ssh_private_key_file=$AUTOINSTALL_SSH_PRIVATE_KEY_FILE" \
  -var "profile=$profile" .
source_image="$(find "$output_dir" -type f -size +1M -not -name '*.log' -print -quit)"
[[ -n "$source_image" ]] || { echo "ERROR: Packer completed without a disk artifact" >&2; exit 1; }
target_image="$output_dir/ubuntu-${release}-${arch}.${format}"
qemu-img convert -O "$format" "$source_image" "$target_image"
sha256sum "$target_image" > "$target_image.sha256"
python3 "$ROOT_DIR/scripts/release/generate-metadata.py" --artifact "$target_image" --release "$release" --architecture "$arch" --type "$format" --output "$target_image.metadata.json"
echo "VM build complete: $output_dir"
