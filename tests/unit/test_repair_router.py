import unittest
from unittest.mock import patch

from scripts.automation.repair_router import CLAUDE_DISPATCH_MARKER, GitHubAPI, route, task_from_event


REPOSITORY = "berttoli/ubuntu-image-factory-management"


def repository_event():
    return {"repository": {"full_name": REPOSITORY, "default_branch": "main"}}


def failed_workflow_event(**overrides):
    run = {
        "conclusion": "failure",
        "name": "validate",
        "id": 42,
        "html_url": f"https://github.com/{REPOSITORY}/actions/runs/42",
        "head_branch": "main",
        "head_sha": "abc",
        "head_repository": {"full_name": REPOSITORY},
        "pull_requests": [],
    }
    run.update(overrides)
    return repository_event() | {"action": "completed", "workflow_run": run}


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
        task = task_from_event("workflow_run", failed_workflow_event(), REPOSITORY)
        self.assertEqual(task.key, "workflow-validate-main")
        self.assertIn("actions/runs/42", task.body)

    def test_external_fork_workflow_failure_is_ignored(self):
        event = failed_workflow_event(
            head_branch="untrusted-fix",
            head_repository={"full_name": "contributor/fork"},
            pull_requests=[],
        )
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))

    def test_agent_authored_runs_are_ignored(self):
        event = failed_workflow_event(actor={"login": "claude[bot]"})
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))
        event = failed_workflow_event(head_branch="claude/issue-14")
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))

    def test_successful_workflow_is_ignored(self):
        event = repository_event() | {"action": "completed", "workflow_run": {"conclusion": "success"}}
        self.assertIsNone(task_from_event("workflow_run", event, REPOSITORY))

    def test_repository_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            task_from_event("workflow_run", repository_event(), "attacker/repository")

    def test_new_repair_issue_dispatches_claude_once(self):
        task_body = "reported failure\n<!-- repair-router:workflow-validate-main -->\n"
        created = {"number": 7, "body": task_body}
        with patch.object(GitHubAPI, "find_open_issue", return_value=None), patch.object(
            GitHubAPI, "create_issue", return_value=created
        ), patch.object(GitHubAPI, "dispatch_claude") as dispatch, patch.object(
            GitHubAPI, "mark_dispatched"
        ) as mark:
            result = route("workflow_run", failed_workflow_event(), REPOSITORY, "token")
        self.assertEqual(result, "repair issue #7 dispatched to Claude")
        dispatch.assert_called_once_with(7)
        mark.assert_called_once_with(7, task_body)

    def test_existing_unqueued_issue_is_dispatched(self):
        existing = {"number": 8, "body": "old repair issue"}
        with patch.object(GitHubAPI, "find_open_issue", return_value=existing), patch.object(
            GitHubAPI, "dispatch_claude"
        ) as dispatch, patch.object(GitHubAPI, "mark_dispatched") as mark:
            result = route("workflow_run", failed_workflow_event(), REPOSITORY, "token")
        self.assertEqual(result, "repair issue #8 dispatched to Claude")
        dispatch.assert_called_once_with(8)
        mark.assert_called_once_with(8, "old repair issue")

    def test_previously_dispatched_issue_is_not_queued_again(self):
        existing = {"number": 8, "body": f"old issue\n{CLAUDE_DISPATCH_MARKER}"}
        with patch.object(GitHubAPI, "find_open_issue", return_value=existing), patch.object(
            GitHubAPI, "dispatch_claude"
        ) as dispatch:
            result = route("workflow_run", failed_workflow_event(), REPOSITORY, "token")
        self.assertEqual(result, "repair issue #8 already dispatched to Claude")
        dispatch.assert_not_called()

    def test_github_api_accepts_empty_204_response(self):
        class EmptyResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b""

        api = GitHubAPI(REPOSITORY, "token")
        with patch("scripts.automation.repair_router.urllib.request.urlopen", return_value=EmptyResponse()):
            self.assertIsNone(api.request("POST", f"/repos/{REPOSITORY}/dispatches", {"event_type": "claude_repair"}))

    def test_dispatch_payload_targets_only_the_repair_workflow(self):
        api = GitHubAPI(REPOSITORY, "token")
        with patch.object(GitHubAPI, "request") as request:
            api.dispatch_claude(51)
        request.assert_called_once_with(
            "POST",
            f"/repos/{REPOSITORY}/dispatches",
            {"event_type": "claude_repair", "client_payload": {"issue_number": 51}},
        )


if __name__ == "__main__":
    unittest.main()
