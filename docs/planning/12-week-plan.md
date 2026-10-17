# 12-week implementation plan

The plan assumes one primary maintainer and GitHub-hosted Linux runners. Each week ends with a reviewable artifact or evidence record.

| Week | Outcome | Acceptance evidence |
| --- | --- | --- |
| 1 | Baseline audit, repository governance, and evidence contract | `AGENTS.md`, audit report, baseline, backlog, architecture, policy; `make audit` passes. |
| 2 | Pin CI/build dependencies and correct repository identity | Immutable action/tool pins, concrete CODEOWNERS/OCI source, dependency checks pass. |
| 3 | Make VM build reproducible on a Linux runner | 26.04 amd64 QCOW2/RAW build with recorded tool/base/ISO metadata. |
| 4 | Add VM boot/security acceptance tests | QEMU/Goss assertions cover cloud-init, SSH, services, firewall, identity cleanup. |
| 5 | Validate 24.04 compatibility | Same VM evidence and documented release-specific differences. |
| 6 | Complete bare-metal ISO integration | QEMU installer test for minimal/hardened profiles and destructive-disk safety. |
| 7 | Complete OCI multi-architecture build | Both architectures build/run non-root; SBOM and digest evidence attached. |
| 8 | Enforce vulnerability and provenance gates | Negative-path tests prove scanner/feed/signature failures block publication. |
| 9 | Add observability and release evidence | Structured build events, provenance, checksums, SBOM, signature, and manifest are correlated. |
| 10 | Reproducibility and dependency maintenance | Repeat-build comparison, immutable pins, and automated update review. |
| 11 | Operational recovery and lifecycle runbooks | Rollback, SSH recovery, incident response, host/container maintenance procedures reviewed. |
| 12 | Production-readiness review | All P0 items have execution evidence; unresolved risks are accepted explicitly or remain blocked. |

No new portfolio repository should be created before week 4 evidence is reviewed. The next projects depend on this factory demonstrating ownership, not merely containing workflow files.
