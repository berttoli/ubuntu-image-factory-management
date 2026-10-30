# Claude repair automation

The `agent-repair-router` workflow creates or reuses one issue for a new Dependabot PR or eligible failed workflow. It dispatches `claude-repair` through GitHub's repository dispatch API. Claude investigates the issue using the trusted default-branch checkout and available Actions logs, then leaves a change on a `claude/` branch. The workflow opens a draft PR for human review. It never merges, publishes, or deploys.

The router ignores successful runs, Claude-authored runs, Claude branches, and failed workflows for pull requests from forks. A marker in each issue prevents repeated failures from dispatching duplicate Claude tasks. Previously created, undispatched repair issues can be started through the `claude-repair` workflow's manual dispatch input.

## One-time repository setup

1. Install the [Claude Code GitHub App](https://github.com/apps/claude) for this repository. Confirm its repository permissions allow reading Actions runs and logs, creating branches, and opening pull requests.
2. Add an Anthropic API key as the repository Actions secret `ANTHROPIC_API_KEY`. The key is used only by `claude-repair`; never store it in repository files or workflow inputs. An OAuth token or workload identity federation can be configured instead by changing the Claude action inputs.
3. Keep the workflow's `id-token: write`, `actions: read`, `contents: write`, `issues: write`, and `pull-requests: write` permissions. The router separately needs `contents: write` to dispatch Claude and `issues: write` to manage repair issues.
4. Require the validation checks and human review for merging Claude draft PRs. Do not enable auto-merge.
5. In repository **Settings → Actions → General → Workflow permissions**, enable **Allow GitHub Actions to create and approve pull requests** if the workflow token will open draft PRs. This setting permits PR creation; the workflow still requests `pull-requests: write` explicitly and never approves a PR.
6. Run a manual smoke test by dispatching `claude-repair` with an open router-created issue number. Confirm the action reads the task, creates a `claude/` branch, opens a draft PR, and CI runs on that PR.

The workflow checks `ANTHROPIC_API_KEY` before invoking Claude so a missing credential fails with a specific setup error. The draft PR step uses the workflow's GitHub token; the Claude action may revoke its own app token during cleanup. If Claude still fails after the credential check, inspect that run's action logs and GitHub App permissions before retrying. Public job metadata alone does not identify an API, billing, permission, or action-internal failure.

No Copilot entitlement or `COPILOT_ASSIGNMENT_TOKEN` is used. Claude API usage is billed by Anthropic under the configured credential.

## Routing and safety

| Event | Result |
| --- | --- |
| Dependabot PR opened or reopened | Create/reuse a repair issue and dispatch Claude once for that issue. |
| Eligible failed Actions run | Create/reuse a repair issue and dispatch Claude once for that issue. |
| Failed workflow from a fork PR | Ignore it; do not run an agent with repository write access on external PR content. |
| Successful run, Claude-authored run, or `claude/` branch | Ignore it to prevent unnecessary work and repair loops. |

The router does not check out triggering PR code. The Claude workflow checks out the default branch only. Issue text, PR metadata, and logs are untrusted evidence; the agent instructions forbid treating them as authority. The action's generated branch is restricted to the `claude/` prefix before the workflow creates a draft PR.

The action receives read access to Actions logs and write access needed to prepare a repair branch and pull request. All generated PRs remain drafts and require normal CI and human review.

## Verification

Run `make validate`, `make test`, and `make audit`. Unit tests cover event filtering, fork rejection, issue deduplication, dispatch idempotency, and response handling. They cannot verify Anthropic credentials, Claude App installation permissions, or remote PR creation; a GitHub smoke test is required for those capabilities.

References: [Claude Code Action setup](https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md), [usage and supported inputs](https://github.com/anthropics/claude-code-action/blob/main/docs/usage.md), [action security guidance](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md), [GitHub workflow triggering rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
