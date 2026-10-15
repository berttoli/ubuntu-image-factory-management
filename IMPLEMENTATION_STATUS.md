# Implementation status

Updated: 2026-10-15

## Current state

This repository was empty at project start. The factory is now scaffolded as a functional, configuration-driven platform with local validation/tests, target-specific build entry points, and GitHub Actions release gates.

| Area | Status | Evidence / limitation |
| --- | --- | --- |
| Release configuration | Implemented | `configs/factory.yaml`, schema, release overrides |
| Shared security policy | Implemented | `configs/security/baseline.yaml`, VM provisioning, Ansible role |
| VM Packer path | Implemented | `packer/`, `scripts/build/build-vm.sh`; requires Linux/QEMU/Packer and AAVMF firmware for arm64 |
| QCOW2/RAW conversion | Implemented | `qemu-img convert` in VM build script |
| Bare-metal autoinstall | Implemented | Rendered autoinstall templates and ISO builder; requires Ubuntu ISO tooling |
| OCI build | Implemented | `containers/Dockerfile`, buildx script |
| SBOM/scanning/signing | Implemented as gated steps | Requires Syft, Trivy, Cosign and CI credentials for publication |
| CI validation/monitoring/build/release | Implemented | Required workflow files present |
| Local unit tests | Verified | Python standard-library unittest suite |
| Local VM boot test | Blocked on host | macOS ARM64 host has no QEMU/Packer installed |
| Local ISO build/install test | Blocked on host | `xorriso`, ISO tooling, and Linux installer execution unavailable |
| Local vulnerability scan | Blocked on host | Trivy/Syft not installed; CI installs pinned tools |
| Local container build | Blocked on host | Docker Buildx is installed, but the Docker daemon socket is unavailable |
| GitHub publication | Not attempted | Requires a remote repository, GHCR permissions, and OIDC/Cosign setup |

## Decisions

1. Packer/QEMU is the primary generic VM path. Canonical imagecraft/ubuntu-image remain optional references for bootable/classical image work and are not hidden runtime dependencies.
2. Ubuntu 26.04.1 and 24.04.5 are the tracked point releases as of this document date. ISO URLs/checksum files are authoritative release metadata and are refreshed by monitoring workflows.
3. Autoinstall storage requires a target disk serial. This prevents a generic ISO from silently selecting and erasing an arbitrary disk.
4. Release artifacts are content-addressed in metadata and are never overwritten. Moving a channel pointer requires a new signed manifest.
5. Missing security tooling is a hard failure for promotion; local development can still run configuration/unit validation.

## Remaining verification procedure

On an Ubuntu 24.04/26.04 runner with nested virtualization or a QEMU-capable host:

```bash
make preflight
make validate test
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=qcow2
make test-vm IMAGE=build/vm/ubuntu-26.04-amd64.qcow2
make build-iso RELEASE=26.04 ARCH=amd64 PROFILE=hardened \
  AUTOINSTALL_TARGET_DISK_SERIAL='FACTORY-QEMU-DISK'
make build-container RELEASE=26.04 ARCH=amd64
make security ARTIFACT=build/container
```

The CI workflow `test-images.yml` is the canonical boot-test procedure and must be green before stable promotion.

## Verification log

- `make validate`: passed; Packer and ShellCheck checks were explicitly deferred because those binaries are absent locally.
- `make test`: passed, 8 tests.
- Bash syntax checks: passed for all shell scripts.
- Python compile checks: passed for scripts and tests.
- `make preflight`: passed required host checks; reported target-specific tools as unavailable.
- `make build-vm`: refused with the expected missing-Packer error.
- `make build-iso`: refused with the expected missing-xorriso error.
- `make build-container`: refused with the expected unavailable-Docker-daemon error.
- `make security`: refused with the expected missing-Trivy error; no empty report was produced.
- Git repository initialization/commit: unavailable because the workspace exposes `.git` as read-only/special and does not permit creating repository metadata.
