# Bare-metal deployment

1. Create a deployment-specific password hash and obtain an SSH public key through your approved secret-handling process.
2. Identify the exact target disk serial from the machine inventory. Do not guess `/dev/sda`, `/dev/nvme0n1`, or use a largest-disk selector.
3. Render and review the seed:

```bash
export AUTOINSTALL_PASSWORD_HASH='generated-outside-git'
export AUTOINSTALL_SSH_PUBLIC_KEY='ssh-ed25519 ...'
export AUTOINSTALL_TARGET_DISK_SERIAL='inventory-serial'
make build-iso RELEASE=26.04 ARCH=amd64 PROFILE=hardened
```

4. Verify the `.sha256` file and write the ISO to USB using a reviewed device path. Writing an ISO to the wrong device destroys data.
5. Boot using UEFI where available. BIOS compatibility is retained by the ISO boot layout where the source ISO supports it.

Encrypted storage is not enabled by the generic profile. Use `autoinstall/profiles/encrypted.yaml` only after approving unlock, recovery, and key escrow procedures.

