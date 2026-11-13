#!/usr/bin/env bash
# Acceptance test for a built VM image.
#
#   scripts/test/test-vm.sh <image.qcow2|image.raw>
#
# Boots the image the way a deployment would: untouched (QEMU -snapshot, so the artifact
# is never modified), with a NoCloud seed that supplies a one-off verifier account. It
# then logs in over SSH and checks first-boot identity, the security baseline and, for
# sealed images, that no build credential survived.
#
#   EXPECT_SEALED=0          skip the sealed-credential checks (images built with
#                            operator-supplied credentials)
#   BOOT_TIMEOUT_SECONDS     seconds to wait for SSH (default 600; emulation is slow)
#   TEST_EVIDENCE_DIR        keep the serial log and check results here
set -Eeuo pipefail

image="${1:?image path required}"
arch="${ARCH:-amd64}"
expect_sealed="${EXPECT_SEALED:-1}"
timeout_seconds="${BOOT_TIMEOUT_SECONDS:-600}"

if [[ "$arch" == arm64 ]]; then
  qemu_bin=qemu-system-aarch64
  qemu_machine=(-machine virt -cpu max -bios /usr/share/AAVMF/AAVMF_CODE.fd)
else
  qemu_bin=qemu-system-x86_64
  qemu_machine=(-machine q35)
fi
qemu_accel=()
if [[ -w /dev/kvm && "$arch" == amd64 ]]; then qemu_accel=(-enable-kvm -cpu host); fi
command -v "$qemu_bin" >/dev/null 2>&1 || { echo "SKIP: $qemu_bin is not installed"; exit 77; }
for tool in cloud-localds ssh ssh-keygen; do
  command -v "$tool" >/dev/null 2>&1 || { echo "ERROR: $tool is required (cloud-image-utils, openssh-client)" >&2; exit 1; }
done
[[ -f "$image" ]] || { echo "ERROR: image not found: $image" >&2; exit 1; }
case "$image" in *.qcow2) image_format=qcow2 ;; *) image_format=raw ;; esac

tmp_dir="$(mktemp -d)"
evidence_dir="${TEST_EVIDENCE_DIR:-$tmp_dir/evidence}"
mkdir -p "$evidence_dir"
serial_log="$evidence_dir/serial.log"
qemu_pid=""
cleanup() {
  [[ -n "$qemu_pid" ]] && kill "$qemu_pid" 2>/dev/null || true
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

ssh-keygen -q -t ed25519 -N '' -C factory-verifier -f "$tmp_dir/verifier"
cat >"$tmp_dir/user-data" <<SEED
#cloud-config
users:
  - name: verifier
    shell: /bin/bash
    sudo: 'ALL=(ALL) NOPASSWD:ALL'
    ssh_authorized_keys:
      - $(cat "$tmp_dir/verifier.pub")
SEED
printf 'instance-id: factory-acceptance-%s\nlocal-hostname: factory-acceptance\n' "$(date +%s)" >"$tmp_dir/meta-data"
cloud-localds "$tmp_dir/seed.iso" "$tmp_dir/user-data" "$tmp_dir/meta-data"

port="$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
"$qemu_bin" "${qemu_accel[@]}" "${qemu_machine[@]}" -m 2048 -smp 2 -display none -snapshot \
  -drive "file=$image,if=virtio,format=$image_format" \
  -drive "file=$tmp_dir/seed.iso,if=virtio,format=raw,readonly=on" \
  -nic "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:${port}-:22" \
  -serial "file:$serial_log" -no-reboot &
qemu_pid=$!

remote() {
  ssh -i "$tmp_dir/verifier" -p "$port" -o BatchMode=yes -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR \
    verifier@127.0.0.1 "$@"
}

echo "waiting up to ${timeout_seconds}s for SSH on the booted image"
deadline=$((SECONDS + timeout_seconds))
until remote true 2>/dev/null; do
  if ! kill -0 "$qemu_pid" 2>/dev/null; then
    echo "ERROR: QEMU exited before the image accepted SSH" >&2
    tail -n 60 "$serial_log" >&2 || true
    exit 1
  fi
  if ((SECONDS >= deadline)); then
    echo "ERROR: no SSH after ${timeout_seconds}s" >&2
    tail -n 60 "$serial_log" >&2 || true
    exit 1
  fi
  sleep 3
done
remote 'cloud-init status --wait' >"$evidence_dir/cloud-init-status.txt" 2>&1 || true

failures=0
check() {  # check <description> <command run on the image>
  if remote "$2" >/dev/null 2>&1; then
    echo "PASS  $1" | tee -a "$evidence_dir/results.txt"
  else
    echo "FAIL  $1" | tee -a "$evidence_dir/results.txt"
    failures=$((failures + 1))
  fi
}
: >"$evidence_dir/results.txt"

check "machine-id was generated on first boot" 'test "$(wc -c </etc/machine-id)" -ge 32'
check "SSH host keys were generated on first boot" 'ls /etc/ssh/ssh_host_ed25519_key.pub'
check "cloud-init finished without errors" 'cloud-init status | grep -q "status: done"'
check "sshd: password login is off" 'sudo sshd -T | grep -qx "passwordauthentication no"'
check "sshd: root login is off" 'sudo sshd -T | grep -qx "permitrootlogin no"'
check "sshd: keyboard-interactive login is off" 'sudo sshd -T | grep -qx "kbdinteractiveauthentication no"'
check "firewall is active" 'sudo ufw status | grep -q "^Status: active"'
check "firewall denies inbound by default" 'sudo ufw status verbose | grep -q "deny (incoming)"'
check "AppArmor is enabled" 'sudo aa-status --enabled'
check "auditd is running" 'systemctl is-active --quiet auditd'
check "unattended-upgrades is enabled" 'systemctl is-enabled --quiet unattended-upgrades'
check "kernel pointers are restricted" 'test "$(sysctl -n kernel.kptr_restrict)" = 2'
check "dmesg is restricted" 'test "$(sysctl -n kernel.dmesg_restrict)" = 1'
check "only SSH listens on a non-loopback address" '! sudo ss -Hltn | awk "{print \$4}" | grep -vE "^(127\.|\[::1\]|.*:22$)" | grep -q .'
if [[ "$expect_sealed" == 1 ]]; then
  check "sealed: no build key is authorised" '! sudo test -s /home/factory/.ssh/authorized_keys'
  check "sealed: the build password is locked" 'sudo passwd -S factory | awk "{print \$2}" | grep -qx L'
  check "sealed: build-time sudo was removed" '! sudo test -e /etc/sudoers.d/90-factory-build'
fi
remote 'uname -r; . /etc/os-release; echo "$PRETTY_NAME"; sudo ss -Hltnu' >"$evidence_dir/system.txt" 2>&1 || true

kill "$qemu_pid" 2>/dev/null || true
qemu_pid=""
if ((failures > 0)); then
  echo "VM acceptance test failed: $failures check(s)" >&2
  exit 1
fi
echo "VM acceptance test passed"
