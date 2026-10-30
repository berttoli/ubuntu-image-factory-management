# Implementation status

Updated: 2026-10-30

## Current state

This repository was empty at project start. The factory now has a configuration-driven implementation, local validation/tests, target-specific build entry points, GitHub Actions release gates, and a machine-verifiable portfolio audit. Artifact production remains partially unverified until Linux/QEMU/Docker/security-tool execution evidence is captured.

| Area | Status | Evidence / limitation |
| --- | --- | --- |
| Release configuration | Implemented | `configs/factory.yaml`, schema, release overrides |
| Shared security policy | Implemented | `configs/security/baseline.yaml`, VM provisioning, Ansible role |
| VM Packer path | Implemented | `packer/`, `scripts/build/build-vm.sh`; requires Linux/QEMU/Packer and AAVMF firmware for arm64 |
| QCOW2/RAW conversion | Implemented | `qemu-img convert` in VM build script |
| Bare-metal autoinstall | Implemented | Rendered autoinstall templates and ISO builder; requires Ubuntu ISO tooling |
| OCI build | Implemented | `containers/Dockerfile`, buildx script |
| SBOM/scanning/signing | Implemented as gated steps | Requires Syft, Trivy, Cosign and CI credentials for publication |
| CI validation/monitoring/build/release | Implemented | Required workflow files present; upstream monitor validates all configured ISO checksums and runner labels, while security-feed changes request candidate VM and OCI rebuilds |
| Portfolio baseline and evidence audit | Verified | `make audit`, typed `scripts/audit/repository_audit.py`, JSON/Markdown report, structural audit test |
| Claude repair routing | Implemented, unverified remotely | Issue router and Claude workflow are locally tested; Anthropic API key, Claude GitHub App installation, and remote branch/PR behavior require a smoke test |
| Local unit tests | Verified | Python standard-library unittest suite; 27 tests pass |
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

The CI workflow `test-images.yml` validates source and tool prerequisites. `build-vm.yml` invokes a QEMU serial-log cloud-init smoke test. Neither currently proves SSH access, expected services, firewall policy, or first-boot identity regeneration; the planned week-4 VM acceptance test remains outstanding and is required before stable promotion.

## Verification log

- 2026-10-30 factory follow-up (branch `fix/monitor-build-readiness`): carried forward the monitor issue-evidence update and added credential-aware VM rebuild dispatch. The security monitor now records a VM credential blocker while still requesting OCI candidates. Claude repair now checks for `ANTHROPIC_API_KEY` before invoking the action and uses the workflow GitHub token for its later draft-PR step; the action's own app token may be revoked during cleanup. Local `make audit`, `make validate`, `make test` (32 tests), Ruby syntax, and diff checks passed. Remote monitor, Claude, and VM boot behavior remain unverified until the branch is run in Actions; missing build secrets still block scheduled VM/bare-metal workflows.
- VM artifact selection is now limited to the matching Packer output directory and requires exactly one disk. This prevents a RAW conversion from silently selecting an earlier QCOW2 artifact in the shared build tree. A full Packer build was not executable on this macOS host; script syntax and workflow contract checks are local evidence only.
- Next repository design is recorded at `docs/portfolio/agentic-platform-engineering-plan.md`. It is a proposal only. Repository creation remains gated on reviewed Ubuntu 26.04 VM boot/security evidence.

- 2026-10-30 Actions/issue review: [Dependabot PR #31](https://github.com/berttoli/ubuntu-image-factory-management/pull/31) validation passed; [PR #32](https://github.com/berttoli/ubuntu-image-factory-management/pull/32) validation failed in `make test` after changing only the pinned Claude action SHA. The old test required the superseded SHA; it now verifies a full 40-character pin. The fixture-only artifact-name test was removed because it exercised no repository behavior. The new assertion was checked against PR #32's actual workflow file. `make audit`, `make validate`, `make test` (27 tests), and `git diff --check` passed locally.
- 2026-10-30 external blockers: the latest [VM build runs](https://github.com/berttoli/ubuntu-image-factory-management/actions/runs/41049476125) fail at `Materialize ephemeral SSH key file`, before QEMU installation; repository build credentials remain required. [Claude repair runs](https://github.com/berttoli/ubuntu-image-factory-management/actions/runs/40830227223) fail in the Claude action step; public job metadata does not provide the underlying log error. Open issues #29/#30 track build credentials, #33/#34 track Dependabot reviews, and #6/#7 track upstream metadata/security-feed review. No remote check or issue was changed by this local commit.
- 2026-10-26 monitor improvement (branch `fix/actionable-monitor-issues`): upstream/security monitors now refresh open issues with current checksums, feed digests, and run links while preserving human notes. `refresh_issue=true` permits updating existing issues #6/#7 without dispatching builds on an already-seen feed. Unseen feed digests still request candidate builds; issue updates do not imply scanner or promotion success. Local `make test` (33 tests), `make validate`, `make audit`, `ruby -c`, and live upstream checksum validation passed. GitHub issue updates and CI dispatch remain unverified until this branch runs remotely.

- `make validate`: passed; Packer and ShellCheck checks were explicitly deferred because those binaries are absent locally.
- `make test`: passed, 27 tests.
- `ansible-lint ansible`: passed with zero findings.
- `actionlint`: passed for all GitHub Actions workflows, including the Claude repair dispatcher.
- `yamllint -c .yamllint.yml .github/workflows ansible autoinstall configs containers`: passed.
- Claude repair routing: unit tests cover dispatch, deduplication, fork filtering, action contract, and empty dispatch responses. Remote Anthropic credentials, Claude App permissions, and PR creation remain unverified until a GitHub smoke test.
- `make audit`: passed; structural checks and `make validate`/`make test` gates passed; target-specific tool availability recorded in `artifacts/audit/portfolio-audit.json`.
- `scripts/monitor/check_upstream.rb`: live validation passed against Canonical 26.04.1/24.04.5 amd64 and arm64 checksum manifests and the Actions runner metadata; digest `408ddc214e19db8081ae9a4777d8dc3560c15aa1f886923e8b15288ee57094d3`.
- Bash syntax checks: passed for all shell scripts.
- Python compile checks: passed for scripts and tests.
- `make preflight`: passed required host checks; reported target-specific tools as unavailable.
- `make build-vm`: refused with the expected missing-Packer error.
- `make build-iso`: refused with the expected missing-xorriso error.
- `make build-container`: refused with the expected unavailable-Docker-daemon error.
- `make security`: refused with the expected missing-Trivy error; no empty report was produced.
