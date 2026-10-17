import unittest
from unittest.mock import patch

from scripts.automation.repair_router import COPILOT_LOGIN, GitHubAPI, RepairTask, route, task_from_event


REPOSITORY = "berttoli/ubuntu-image-factory-management"


def repository_event():
    return {"repository": {"full_name": REPOSITORY, "default_branch": "main"}}


class RepairRouterTests(unittest.TestCase):
    def test_dependabot_event_creates_scoped_task(self):
        event = repository_event() | {
            "action": "opened",
            "pull_request": {
                "number": 18,
                "html_url": f"https://github.com/{REPOSITORY}/pull/18",
                "title": "Bump checkout",
                "user": {"login": "dependabot[bot]"},
            },
        }
        task = task_from_event("pull_request_target", event, REPOSITORY)
        self.assertEqual(task.key, "dependabot-pr-18")
        self.assertEqual(task.base_branch, "main")
        self.assertIn("pull/18", task.body)

    def test_non_dependabot_pr_is_ignored(self):
        event = repository_event() | {
            "action": "opened",
            "pull_request": {"user": {"login": "human"}},
        }
        self.assertIsNone(task_from_event("pull_request_target", event, REPOSITORY))

    def test_failed_workflow_creates_scoped_task(self):
        event = repository_event() | {
            "action": "completed",
            "workflow_run": {
                "conclusion": "failure",
                "name": "validate",
                "id": 42,
                "html_url": f"https://github.com/{REPOSITORY}/actions/runs/42",
                "head_branch": "main",
                "head_sha": "abc",
                "pull_requests": [],
            },
        }
        task = task_from_event("workflow_run", event, REPOSITORY)
        self.assertEqual(task.key, "workflow-validate-main")
        self.assertIn("actions/runs/42", task.body)

    def test_successful_workflow_is_ignored(self):
        event = repository_event() | {"action": "completed", "workflow_run": {"conclusion": "success"}}
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))

    def test_agent_workflow_failure_is_ignored_to_prevent_loop(self):
        event = repository_event() | {
            "action": "completed",
            "workflow_run": {"conclusion": "failure", "actor": {"login": "copilot-swe-agent[bot]"}},
        }
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))

    def test_repository_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            task_from_event("workflow_run", repository_event(), "attacker/repository")

    def test_existing_issue_is_reused_and_assigned_with_custom_agent(self):
        event = repository_event() | {
            "action": "completed",
            "workflow_run": {
                "conclusion": "failure",
                "name": "validate",
                "id": 42,
                "html_url": "https://github.com/berttoli/ubuntu-image-factory-management/actions/runs/42",
                "head_branch": "main",
                "pull_requests": [],
            },
        }
        existing = {"number": 7, "assignees": [], "body": "<!-- repair-router:workflow-validate-main -->"}
        with patch.object(GitHubAPI, "find_open_issue", return_value=existing), patch.object(
            GitHubAPI, "create_issue"
        ) as create, patch.object(GitHubAPI, "request") as request:
            result = route("workflow_run", event, REPOSITORY, "issue-token", "agent-token")
        create.assert_not_called()
        self.assertEqual(result, "issue #7 assigned to factory-repair")
        method, path, payload = request.call_args.args
        self.assertEqual(method, "POST")
        self.assertEqual(path, f"/repos/{REPOSITORY}/issues/7/assignees")
        self.assertEqual(payload["assignees"], [COPILOT_LOGIN])
        self.assertEqual(payload["agent_assignment"]["custom_agent"], "factory-repair")

    def test_missing_agent_token_keeps_issue_visible(self):
        event = repository_event() | {
            "action": "opened",
            "pull_request": {
                "number": 18,
                "html_url": f"https://github.com/{REPOSITORY}/pull/18",
                "user": {"login": "dependabot[bot]"},
            },
        }
        with patch.object(GitHubAPI, "find_open_issue", return_value=None), patch.object(
            GitHubAPI, "create_issue", return_value={"number": 8, "assignees": []}
        ) as create:
            with self.assertRaisesRegex(RuntimeError, "COPILOT_ASSIGNMENT_TOKEN is missing"):
                route("pull_request_target", event, REPOSITORY, "issue-token", "")
        create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
