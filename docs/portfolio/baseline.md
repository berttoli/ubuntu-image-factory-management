# Portfolio baseline

Status labels used in this document:

- **Verified:** executed locally or against a named live source, with recorded output.
- **Implemented, unverified:** code and workflow paths exist, but the target execution has not completed.
- **Blocked:** execution was attempted and stopped by a named missing capability.
- **Not attempted:** requires external authorization, GitHub-hosted execution, or release credentials.

## Capability inventory

| Capability | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Central release configuration for Ubuntu 26.04 and 24.04 | Verified | `make validate`; `configs/factory.yaml`; schema/config checks | Configuration correctness is verified; package/image builds are separate evidence. |
| Shared host/container security policy | Verified statically | `make test`; `configs/security/baseline.yaml`; 3 security tests | Runtime enforcement on a booted host has not been demonstrated locally. |
| Autoinstall rendering and destructive-disk guard | Implemented, unverified end-to-end | `scripts/autoinstall/render.py`; runtime marker tests | ISO installation on a virtual disk remains unverified. |
| Packer QEMU VM path | Implemented, blocked locally | `scripts/build/build-vm.sh`; attempted `make build-vm` | Packer, QEMU, and guest firmware are unavailable on this host. |
| QCOW2 and RAW conversion | Implemented, unverified | `qemu-img convert` in the VM build path | Requires a completed Packer build and artifact inspection. |
| Bare-metal ISO generation | Implemented, blocked locally | `scripts/build/build-iso.sh`; attempted `make build-iso` | `xorriso` and Linux installer execution are unavailable locally. |
| OCI image build | Implemented, blocked locally | `containers/Dockerfile`; attempted `make build-container` | Docker CLI exists, but the daemon is unavailable. |
| SBOM and vulnerability gate | Implemented as a fail-closed path, blocked locally | `scripts/security/scan.sh`; attempted `make security` | Syft and Trivy are unavailable; no empty report is accepted. |
| Signing and provenance | Implemented in release workflow, not attempted | `.github/workflows/release.yml` | Requires GitHub OIDC, GHCR, release permissions, and a successful artifact build. |
| Upstream checksum monitoring | Verified | Live `scripts/monitor/check_upstream.rb` run passed for four ISO entries and runner labels | Monitoring detects drift; it does not silently update release configuration. |
| CI workflow execution | Unverified | Workflow YAML parses locally | Requires a GitHub Actions run on the remote repository. |
| Automated audit/evidence report | Verified | `make audit`; `artifacts/audit/portfolio-audit.json` and `.md` | Evidence is ignored build output and must be attached to reviews or CI summaries. |

## Evidence captured on 2026-10-16

```text
make validate  -> passed; 21 YAML files, config, and secret scan passed
make test      -> passed; 11 tests
make preflight -> passed required checks; target-specific tools reported unavailable
make build-vm  -> blocked; Packer unavailable
make build-iso -> blocked; xorriso unavailable
make build-container -> blocked; Docker daemon unavailable
make security  -> blocked; Trivy unavailable
make audit     -> passed; structural checks plus validate/test gates
```

The audit report records the exact commit, branch, tool paths, gate exit codes, and structural checks. A missing optional build tool is evidence of an unverified target, never a successful build.

## Material risks

1. The release workflow is broader than the locally tested code path and currently depends on external tools and credentials.
2. GitHub Action references are versioned tags, not immutable commit SHAs; a compromised or retagged action remains a supply-chain risk.
3. Packer is configured with `version: latest`, which prevents deterministic builder reproduction.
4. The container build installs from a moving Ubuntu tag and obtains SBOM tooling through a remote install script; base and tool digests need recording.
5. Boot tests only look for a cloud-init serial-log phrase and do not yet verify SSH policy, services, firewall behavior, or identity regeneration.
6. No coverage measurement, workflow-level tests, or reproducible artifact comparison is currently enforced.
