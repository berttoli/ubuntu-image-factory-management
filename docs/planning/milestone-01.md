# Milestone 01 — Repository baseline and evidence engine

## Objective

Establish a repeatable, machine-verifiable baseline before expanding artifact production. This milestone does not claim that VM, ISO, OCI, signing, or publication paths are production-ready.

## Implementation

- `AGENTS.md` defines repository-specific agent behavior and safety boundaries.
- `scripts/audit/repository_audit.py` checks required architecture files, workflows, release tracks, Make targets, security-policy markers, fork identity, tool availability, and local gates.
- `make audit` writes ignored JSON and Markdown reports under `artifacts/audit/`.
- `tests/unit/test_repository_audit.py` verifies the structural audit contract.
- Portfolio baseline, backlog, architecture, 12-week plan, and agent policy are documented under `docs/`.

## Acceptance criteria

- [x] Audit is typed Python using only the standard library.
- [x] Audit emits machine-readable JSON and human-readable Markdown.
- [x] Audit fails when required repository structure or identity placeholders are missing/incorrect.
- [x] Audit executes `make validate` and `make test` unless explicitly run with `--skip-gates`.
- [x] `make audit`, `make validate`, and `make test` pass on the current feature branch.
- [x] Missing target-specific tools remain visible in the report.
- [ ] Ubuntu VM, ISO, OCI, scanner, signing, and GitHub workflow execution evidence is intentionally deferred to later milestones.

## Evidence

Run:

```bash
make audit
make validate
make test
```

The generated report is `artifacts/audit/portfolio-audit.json` and is ignored by Git because it is environment- and commit-specific. Attach it to a review or CI job when using it as acceptance evidence.
