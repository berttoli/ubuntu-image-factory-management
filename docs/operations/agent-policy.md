# Agent permission and evaluation policy

Agents are implementation assistants, not release authorities. The repository must remain safe if an agent misunderstands a task.

## Permission matrix

| Action | Default | Conditions |
| --- | --- | --- |
| Read repository files, Git history, local tool state | Allow | Stay within the requested repository/worktree. |
| Create or modify local files on a feature branch | Allow | Use small changes, tests, and reviewable commits. |
| Run local validation, unit tests, dry-run builders | Allow | Do not bypass failures or fabricate unavailable evidence. |
| Read public upstream metadata | Allow | Record source and timestamp; do not silently rewrite tracked configuration. |
| Install packages/tools | Ask | Requires user approval and should use documented, reproducible versions. |
| Push a branch | Ask | User must explicitly authorize the remote and branch. |
| Open/modify/close GitHub issues or pull requests | Ask | Include exact scope and generated content; never close review work automatically. |
| Publish images, releases, signatures, or GHCR tags | Ask | Requires explicit release authorization and passed gates. |
| Change external infrastructure or credentials | Deny by default | Requires explicit scope, approval, and an auditable change plan. |
| Destructive disk, filesystem, or history operations | Deny by default | Require explicit target, confirmation, and recovery path. |

## Evaluation gates

Every milestone is evaluated against:

1. **Correctness:** required tests and machine checks pass.
2. **Evidence:** the report names the command, commit, environment, and result.
3. **Security:** no secrets, broad permissions, mutable release identifiers, or silent scanner failures.
4. **Reproducibility:** configuration and tool versions are explicit enough to repeat the work.
5. **Operability:** failures explain the next action and recovery path.
6. **Reviewability:** changes are isolated, documented, and small enough for a human review.

An unavailable capability is `blocked` or `unverified`, never `passed`. A failed mandatory gate stops the milestone. Exceptions must be written, owned, time-bounded, and linked to a remediation issue.

## Agent handoff format

Each handoff must include:

- branch and commit;
- files changed and why;
- commands executed and exact outcomes;
- capabilities not executed and the blocker;
- security/release implications;
- the smallest next action for a human reviewer.
