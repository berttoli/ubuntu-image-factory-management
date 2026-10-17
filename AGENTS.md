# Agent instructions

## Scope

This repository builds Ubuntu Server installation media, QEMU/KVM disk images, and OCI containers. Treat image production, signing, publication, and deployment as separate trust boundaries.

## Required workflow

1. Work on a feature branch or isolated worktree.
2. Read `IMPLEMENTATION_STATUS.md` and the relevant architecture/security documentation before changing build or release behavior.
3. Make the smallest reviewable change and add or update typed Python tests for new Python behavior.
4. Run `make audit`, `make validate`, and `make test` before handoff. Run target-specific build/security checks when the required host tools are available.
5. Record verified results and blockers in `IMPLEMENTATION_STATUS.md` or the milestone evidence document.

## Safety boundaries

- Never embed passwords, private keys, tokens, or reusable credentials.
- Never broaden unattended disk selection. Physical-media workflows require an explicit disk serial.
- Never publish, sign, deploy, or force-push without explicit authorization.
- Never treat an unavailable scanner, feed, or boot test as a pass.
- Do not claim a target is production-ready without execution evidence for that target.

## Change ownership

- Configuration and policy changes require tests and rationale.
- Workflow changes require least-privilege permissions and pinned, reviewable dependencies.
- Release changes require immutable naming, checksums, SBOM, provenance, signature, and verification evidence.
- Documentation must distinguish implemented, verified, blocked, and unverified capabilities.

## Review checklist

- [ ] Threat model and affected trust boundary identified.
- [ ] Acceptance criteria are executable or linked to a machine-readable check.
- [ ] Failure paths are explicit and actionable.
- [ ] No secrets or mutable release assets added.
- [ ] Local evidence and remaining CI-only evidence documented.
