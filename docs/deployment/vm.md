# VM deployment

Build on Linux with KVM access, Packer, QEMU, `qemu-img`, and network access to Canonical release/package repositories.

```bash
export AUTOINSTALL_EPHEMERAL_CREDENTIALS=1
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=qcow2
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=raw
make test-vm IMAGE=build/vm/ubuntu-26.04-amd64.qcow2
```

## Build credentials

Packer needs to log in to the machine it is installing. With `AUTOINSTALL_EPHEMERAL_CREDENTIALS=1` the build generates a key pair and a random password hash for that one build, and the same command that powers the machine off removes the key, locks the password and deletes the build-time sudo rule. The finished image contains no login credential. This is what CI uses, so no repository secret is needed.

To build with your own credentials instead, leave that variable unset and export `AUTOINSTALL_PASSWORD_HASH`, `AUTOINSTALL_SSH_PUBLIC_KEY` and `AUTOINSTALL_SSH_PRIVATE_KEY_FILE`. Those credentials stay in the image; test it with `EXPECT_SEALED=0`.

## Using the image

The image is a template. On first boot cloud-init regenerates the machine ID and SSH host keys and takes users, keys and network settings from the platform's datasource (NoCloud, ConfigDrive, OpenStack, GCE, EC2 or Azure). Without a datasource nobody can log in, by design.

The RAW build converts the QCOW2 from the same release rather than installing Ubuntu a second time. Set `VM_BUILD_REUSE_QCOW2=0` to force a separate install.

The image uses VirtIO storage/networking and includes `qemu-guest-agent`. For Proxmox, import the RAW/QCOW2 disk into a new VM, attach it as a VirtIO SCSI disk, enable the guest agent, and attach a cloud-init drive. Validate the imported image before production use.

## Acceptance test

`make test-vm` boots the image under QEMU without modifying it, supplies a one-off verifier account through a NoCloud seed, and checks over SSH: first-boot identity, sshd settings, firewall, AppArmor, auditd, unattended upgrades, kernel settings, listening ports, and that no build credential survived. Set `TEST_EVIDENCE_DIR` to keep the serial log and results.
