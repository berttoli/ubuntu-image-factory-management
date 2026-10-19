# Copilot repair agent

The repository custom agent is `.github/agents/factory-repair.agent.md`. GitHub loads repository agents from the default branch. The `agent-repair-router` workflow creates a repair issue for each new Dependabot PR and for failed image-factory workflows. It reuses an existing open issue for the same PR or workflow/branch. When agent assignment is configured, it assigns the issue to Copilot with the `factory-repair` profile. Copilot then works on a branch and requests review through a pull request.

## One-time repository setup

1. Merge the feature branch containing this profile and router into the default branch after review.
2. Enable Copilot cloud agent for this repository and confirm `factory-repair` appears in the agent selector. A paid Copilot plan is required.
3. Create a repository-scoped fine-grained user token with metadata read and actions, contents, issues, and pull requests read/write access, as required by GitHub's Copilot assignment API. Store it as the Actions secret `COPILOT_ASSIGNMENT_TOKEN`. Use a short expiration and rotate it on schedule. The token is used only by the trusted default-branch router workflow.
4. Confirm the repository Actions setting permits pull requests from Copilot and that branch protection requires `validate` and human review. Do not enable auto-merge for agent PRs.
5. Open a small test issue manually and assign `factory-repair` through GitHub's agent selector. Then test the router with a Dependabot PR or a failed workflow run. Check that one issue and one agent task are created, and that its PR carries evidence.

Without the secret, the router still creates an issue and fails visibly so manual `factory-repair` assignment is needed. If the API rejects assignment, the workflow also fails and the issue remains open. The `GITHUB_TOKEN` alone is not sufficient for the Copilot assignment API.

## Routing behavior

| Event | Result |
| --- | --- |
| Dependabot PR opened or reopened | One issue keyed to the PR number; agent reviews the update and opens a separate fix PR only if repository code needs a change. |
| Selected workflow completes with failure | One issue keyed to the workflow and PR/branch; agent investigates the run and opens a fix PR when justified. |
| Successful workflow or non-Dependabot PR | No repair issue. |
| Failed run started by Copilot | No new repair issue; review the existing agent PR and its check results. |

The router runs from the default branch and never checks out the triggering PR or downloads its artifacts. It passes PR titles and run metadata as data in an issue; the agent profile instructs Copilot to treat those fields and logs as untrusted. It does not merge, publish, or deploy.

## Verification

Run `make validate`, `make test`, and `make audit`. For a remote smoke test, inspect the `agent-repair-router` run, its issue, assignment, Copilot task, and resulting PR. Local tests cover event filtering, repository matching, duplicate issue reuse, and the custom-agent assignment payload. They cannot prove Copilot entitlements, token permissions, or the remote agent's PR behavior.

GitHub references: [custom agent tutorial](https://docs.github.com/en/copilot/tutorials/customization-library/custom-agents/your-first-custom-agent), [custom agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration), [cloud agent assignment API](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api).
