#!/usr/bin/env bash
# Turn the freshly installed build machine into a reusable template image.
# Runs as root inside the VM as the last Packer provisioner.
set -Eeuo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERROR: template preparation must run as root" >&2; exit 1; }

# Serial console, so a hypervisor (and the acceptance test) can read the boot.
install -d -m 0755 /etc/default/grub.d
cat >/etc/default/grub.d/60-factory-console.cfg <<'CFG'
GRUB_CMDLINE_LINUX_DEFAULT="console=tty1 console=ttyS0,115200n8"
GRUB_TERMINAL="console serial"
GRUB_SERIAL_COMMAND="serial --speed=115200"
CFG
update-grub

# The installer pins cloud-init to its own one-off seed and takes networking away from
# it. A template must instead accept identity, keys and network from wherever it is
# deployed.
rm -f /etc/cloud/cloud.cfg.d/99-installer.cfg \
      /etc/cloud/cloud.cfg.d/90-installer-network.cfg \
      /etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg \
      /etc/cloud/cloud-init.disabled \
      /etc/cloud/ds-identify.cfg \
      /etc/netplan/00-installer-config.yaml \
      /etc/netplan/50-cloud-init.yaml
cat >/etc/cloud/cloud.cfg.d/95-factory-datasources.cfg <<'CFG'
datasource_list: [NoCloud, ConfigDrive, OpenStack, GCE, Ec2, Azure, None]
CFG

# Per-machine identity is regenerated on first boot.
cloud-init clean --logs --seed
rm -f /etc/ssh/ssh_host_*
truncate -s 0 /etc/machine-id
rm -f /var/lib/dbus/machine-id
apt-get clean
rm -rf /var/lib/apt/lists/*
