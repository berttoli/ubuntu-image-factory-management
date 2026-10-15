# Architecture

The factory has one configuration/security layer and three independent artifact paths.

```text
factory.yaml + security/baseline.yaml
             |
   +---------+-----------+----------------+
   |                     |                |
Packer/QEMU          Autoinstall       OCI Buildx
QCOW2/RAW            ISO/USB           GHCR image
   |                     |                |
boot/security test  installer test   SBOM/Trivy/sign
   +---------------------+----------------+
                         |
                 metadata + checksums
                 provenance + release
```

Packer downloads a Canonical Ubuntu Server ISO using the release-specific URL and SHA-256 entry from the official `SHA256SUMS` file. It serves a rendered NoCloud seed over its temporary HTTP server, installs to a serial-selected virtual disk, applies the baseline, cleans machine identity, and emits a versioned artifact. RAW conversion is deliberately a separate format operation so QCOW2 remains the canonical build output.

The ISO path reuses the same autoinstall seed but is guarded by an explicit disk serial. Generic media therefore cannot accidentally select an arbitrary physical disk. Hardware profiles remain inventory-specific.

Containers use the official `ubuntu:<release>` image, install only CA certificates, create a non-root `factory` user, and do not include SSH or systemd. Host firewall, AppArmor, audit, and unattended-upgrade settings are not copied into the container.

## Trust boundaries

- Canonical release metadata and package signatures are upstream trust roots.
- GitHub Actions OIDC is the signing identity; long-lived signing keys are not stored in repository secrets.
- Build runners are ephemeral. Build metadata records commit, release, architecture, tool/runtime identity, digest/checksum, and scan status.
- Publication occurs only after security gates. Release assets are immutable; a channel promotion creates a new signed manifest.

