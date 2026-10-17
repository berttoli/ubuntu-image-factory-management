# Prioritized engineering backlog

Each item has an acceptance condition that can be checked by a reviewer or CI. Priority reflects risk to trustworthy artifact publication, not feature visibility.

## P0 — required before calling the factory production-oriented

| ID | Work | Acceptance evidence |
| --- | --- | --- |
| UIF-001 | Execute and harden the Ubuntu 26.04 amd64 VM path | GitHub or Linux runner produces QCOW2 and RAW; QEMU boot test verifies cloud-init completion, SSH key login, disabled password/root login, expected services, and machine identity cleanup. |
| UIF-002 | Execute the Ubuntu 24.04 compatibility VM path | Same acceptance suite passes for 24.04; release metadata records exact ISO checksum and package source. |
| UIF-003 | Add real installer-media integration tests | Autoinstall ISO installs into an ephemeral QEMU disk for minimal and hardened profiles; no test uses an unspecified disk selector. |
| UIF-004 | Make supply-chain inputs immutable | Action references, Packer, Syft, Trivy, Cosign, and base-image inputs are pinned to reviewable versions/digests; a dependency job verifies the pins. |
| UIF-005 | Close release-gate correctness gaps | Release cannot publish when boot, scanner, SBOM, provenance, checksum, or signature evidence is absent; a dry-run test proves the negative paths. |
| UIF-006 | Verify OCI artifacts in a real daemon/runner | Both architectures build, run as non-root, contain no SSH/systemd, receive SBOM and vulnerability reports, and are verified by digest before signing. |

## P1 — maintainability and operational confidence

| ID | Work | Acceptance evidence |
| --- | --- | --- |
| UIF-007 | Move build/release orchestration from shell where state is complex | Typed Python command layer has unit tests and preserves explicit failure behavior; shell remains only for thin host adapters. |
| UIF-008 | Add workflow contract tests | Every workflow has validated permissions, action pins, inputs, artifact paths, and required secrets; actionlint runs in CI. |
| UIF-009 | Expand boot security assertions | Goss or equivalent validates packages, listening sockets, SSH settings, UFW, AppArmor, auditd, unattended upgrades, and first-boot identity regeneration. |
| UIF-010 | Implement OpenTelemetry build observability | Build stages emit trace/span or structured event IDs with commit, release, architecture, tool versions, and failure reason without secret values. |
| UIF-011 | Generate changelog and evidence summaries automatically | Release metadata and verified audit results update a reviewable changelog fragment; no generated file can overwrite a stable release. |
| UIF-012 | Add reproducibility checks | Repeated builds under controlled inputs compare normalized metadata and document expected nondeterminism; no bit-for-bit claim is made without proof. |

## P2 — portfolio expansion after P0/P1

| ID | Work | Acceptance evidence |
| --- | --- | --- |
| UIF-013 | Extract reusable agent evaluation framework | A separate, versioned evaluation package tests repository changes against policy, evidence, and security gates without granting publication permissions. |
| UIF-014 | Design `agentic-platform-engineering` | Architecture review, threat model, local development path, typed tests, and one independently verifiable control-plane milestone. |
| UIF-015 | Design `adaptive-data-streams` | Backpressure/ordering model, replayable fixtures, observability, failure injection, and benchmark evidence. |
