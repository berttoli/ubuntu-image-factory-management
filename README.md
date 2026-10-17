# Ubuntu Image Factory

Ubuntu Image Factory is a GitHub-native build and release platform for minimal, security-hardened Ubuntu artifacts:

- unattended Ubuntu Server autoinstall media for physical systems;
- QEMU/KVM QCOW2 and RAW images built with Packer;
- minimal, non-root OCI images published to GHCR.

The repository is designed to be safe by default. Credentials and deployment-specific disk selectors are supplied at render/build time; no passwords, private keys, or broad destructive disk selectors are stored in Git.

## Quick start

```bash
make help
make preflight
make validate
make test
make audit
make build-container
```

The container build is the only artifact build expected to work on this macOS ARM64 development host without additional virtualization tooling. VM and ISO builds require a Linux host or GitHub runner with QEMU/KVM, Packer, `xorriso`, and the supporting tools listed by `make preflight`.

Builds use Ubuntu 26.04.1 LTS by default and support Ubuntu 24.04.5 LTS through the same release configuration. Override with `RELEASE=24.04` and `ARCH=amd64|arm64`.

## Artifact commands

```bash
make build-vm RELEASE=26.04 ARCH=amd64 FORMAT=qcow2
make build-vm RELEASE=24.04 ARCH=amd64 FORMAT=raw
make build-iso RELEASE=26.04 ARCH=amd64 PROFILE=hardened \
  AUTOINSTALL_TARGET_DISK_SERIAL='physical-disk-serial'
make build-container RELEASE=26.04 ARCH=amd64
make test-vm IMAGE=build/vm/ubuntu-26.04-amd64.qcow2
make verify-release MANIFEST=artifacts/release/manifest.json
```

The ISO command intentionally requires an explicit disk serial. For physical deployments, determine the serial with a trusted inventory process and review the rendered configuration before booting media. Encrypted storage is opt-in and requires a deployment-specific key-management plan.

## Security model

The shared policy in `configs/security/baseline.yaml` is applied with target-specific exceptions. Hosts enable SSH key authentication, disable root/password SSH login, configure unattended security updates, restrict core dumps, and enable a default-deny firewall where the target supports it. Containers do not receive host controls such as systemd, UFW, or SSH; they run as an unprivileged user and are scanned and signed independently.

Security scans are promotion gates. Missing scanner binaries or unavailable vulnerability feeds are failures in CI, not successful empty reports.

## CI and releases

The workflows under `.github/workflows/` validate changes, monitor Ubuntu/tooling/security updates, build each target on demand or weekly, and publish immutable releases only after tests, SBOM, provenance, vulnerability checks, and signing complete. Publishing requires repository configuration and credentials; local commands default to dry-run/non-publish behavior.

See `docs/architecture/overview.md`, `docs/architecture/system.md`, `docs/security/baseline.md`, and `docs/operations/release.md` for the design and operating procedures. The portfolio baseline, backlog, 12-week plan, and agent policy are under `docs/portfolio/`, `docs/planning/`, and `docs/operations/agent-policy.md`. `IMPLEMENTATION_STATUS.md` is the source of truth for verified capabilities and blockers.

`make audit` produces ignored JSON and Markdown evidence under `artifacts/audit/`. It checks the repository contract and executes `make validate` and `make test`; missing target-specific tools remain explicit blockers rather than being reported as successful builds.
