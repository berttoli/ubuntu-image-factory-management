# ADR 0001: Establish evidence before expanding artifact production

- Status: accepted
- Date: 2026-10-16
- Owners: `@berttoli`

## Context

The repository contains build paths for VM, bare-metal, and OCI targets, but local execution cannot currently prove all target capabilities. Workflow presence and configuration validity are not equivalent to a production artifact.

## Decision

The first maturity milestone is a typed, standard-library repository audit that verifies the repository contract and executes the local `make validate` and `make test` gates. Artifact-specific milestones must add their own build, boot, security, and provenance evidence before their status changes to verified.

The audit report is generated under ignored `artifacts/audit/` because it contains commit-, host-, and tool-specific evidence. Reviews and CI jobs may attach the report without treating it as source configuration.

## Consequences

- Capability claims become explicit and repeatable.
- Missing tools remain visible as blockers.
- The audit adds a small maintenance surface and must evolve with the repository contract.
- The audit does not replace target-specific integration, security, or release tests.
