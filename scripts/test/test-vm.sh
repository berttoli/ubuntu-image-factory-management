#!/usr/bin/env bash
set -Eeuo pipefail

image="${1:?image path required}"
arch="${ARCH:-amd64}"
if [[ "$arch" == arm64 ]]; then
  qemu_bin=qemu-system-aarch64
  qemu_machine=(-machine virt -cpu max -bios /usr/share/AAVMF/AAVMF_CODE.fd)
else
  qemu_bin=qemu-system-x86_64
  qemu_machine=(-machine q35)
fi
qemu_accel=()
[[ -e /dev/kvm ]] && qemu_accel=(-enable-kvm)
command -v "$qemu_bin" >/dev/null 2>&1 || { echo "SKIP: $qemu_bin is not installed"; exit 77; }
[[ -f "$image" ]] || { echo "ERROR: image not found: $image" >&2; exit 1; }
timeout_seconds="${BOOT_TIMEOUT_SECONDS:-90}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
serial_log="$tmp_dir/serial.log"
"$qemu_bin" "${qemu_accel[@]}" "${qemu_machine[@]}" -m 1024 -smp 2 -nographic \
  -drive "file=$image,if=virtio,format=$(case "$image" in *.qcow2) echo qcow2;; *) echo raw;; esac)" \
  -serial "file:$serial_log" -no-reboot -display none &
qemu_pid=$!
trap 'kill "$qemu_pid" 2>/dev/null || true; rm -rf "$tmp_dir"' EXIT
for _ in $(seq 1 "$timeout_seconds"); do
  if grep -q "cloud-init.*finished" "$serial_log" 2>/dev/null; then
    kill "$qemu_pid" 2>/dev/null || true
    echo "VM boot/cloud-init smoke test passed"
    exit 0
  fi
  if ! kill -0 "$qemu_pid" 2>/dev/null; then
    echo "ERROR: QEMU exited before cloud-init completed" >&2
    cat "$serial_log" >&2 || true
    exit 1
  fi
  sleep 1
done
echo "ERROR: VM boot test timed out after ${timeout_seconds}s" >&2
cat "$serial_log" >&2 || true
kill "$qemu_pid" 2>/dev/null || true
exit 1
