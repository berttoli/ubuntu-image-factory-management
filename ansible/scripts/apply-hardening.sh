#!/usr/bin/env bash
set -Eeuo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERROR: hardening must run as root" >&2; exit 1; }
install -d -m 0755 /etc/ssh/sshd_config.d /etc/sysctl.d /etc/apt/apt.conf.d
cat >/etc/ssh/sshd_config.d/99-factory-hardening.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
X11Forwarding no
MaxAuthTries 3
EOF
cat >/etc/sysctl.d/99-factory-hardening.conf <<'EOF'
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.default.rp_filter=1
kernel.kptr_restrict=2
kernel.dmesg_restrict=1
fs.suid_dumpable=0
EOF
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
cat >/etc/apt/apt.conf.d/52factory-unattended-upgrades <<'EOF'
Unattended-Upgrade::Origins-Pattern {
  "origin=Ubuntu,archive=${distro_codename}-security";
};
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
if command -v ufw >/dev/null 2>&1; then
  ufw --force default deny incoming
  ufw --force default allow outgoing
  ufw --force allow ssh
  ufw --force enable
fi
sysctl --system >/dev/null
systemctl enable apparmor auditd unattended-upgrades ssh 2>/dev/null || true
sshd -t

