# VM deployment

Build on Linux with KVM access, Packer, QEMU, `qemu-img`, and network access to Canonical release/package repositories.

```bash
export AUTOINSTALL_PASSWORD_HASH='generated-outside-git'
export AUTOINSTALL_SSH_PUBLIC_KEY='ssh-ed25519 ...'
export AUTOINSTALL_SSH_PRIVATE_KEY_FILE="$HOME/.ssh/factory-build"
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=qcow2
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=raw
make test-vm IMAGE=build/vm/ubuntu-26.04-amd64-qcow2.qcow2
```

The image uses VirtIO storage/networking and includes `qemu-guest-agent`. For Proxmox, import the RAW/QCOW2 disk into a new VM, attach it as a VirtIO SCSI disk, enable the guest agent, and regenerate the VM-specific identity on first boot. Validate the imported image before production use.
