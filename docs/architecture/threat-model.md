# Threat model

## Assets

- integrity and provenance of released ISO, VM, and OCI artifacts;
- SSH access and runtime credentials supplied by operators;
- Ubuntu package/release inputs and vulnerability status;
- GitHub repository, Actions, Release, and GHCR permissions.

## Threats and controls

| Threat | Control |
| --- | --- |
| Malicious or stale upstream input | Official Canonical URLs and SHA-256 checksums; daily monitoring; pinned release config; security-feed workflow. |
| Secret leakage into an image | No credentials in Git; runtime-only env/file inputs; source secret-pattern tests; machine identity/SSH host-key cleanup. |
| Accidental physical-disk destruction | Autoinstall requires an explicit disk serial and build scripts reject absent selectors. |
| Compromised CI or release token | Least-privilege workflow permissions, ephemeral runners, OIDC keyless Cosign, immutable release assets. |
| Vulnerable dependency/base image | Syft SBOM, Trivy vulnerability/secret/misconfiguration scan, critical/high gates, scheduled rebuilds. |
| Host/container policy confusion | Separate host baseline and container policy; no SSH/systemd in OCI image; target applicability recorded per rule. |
| Artifact substitution | SHA-256 checksums, signed manifest, provenance, digest-based container deployment, release verification command. |

## Residual risks

The factory cannot prove a host remains patched after deployment, cannot certify CIS compliance from these checks alone, and cannot make an offline installer receive security updates unless the operator provides an approved mirror/cache. These are operational controls and are documented as such.

