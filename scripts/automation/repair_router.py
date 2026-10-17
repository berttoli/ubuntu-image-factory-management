#!/usr/bin/env python3
"""Route Dependabot updates and failed Actions runs to the custom repair agent."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


AGENT_ID = "factory-repair"
COPILOT_LOGIN = "copilot-swe-agent[bot]"


@dataclass(frozen=True)
class RepairTask:
    key: str
    title: str
    body: str
    base_branch: str


def task_from_event(event_name: str, event: dict[str, Any], repository: str) -> RepairTask | None:
    repo = event.get("repository", {})
    if repo.get("full_name") != repository or "/" not in repository:
        raise ValueError("event repository does not match GITHUB_REPOSITORY")
    default_branch = str(repo.get("default_branch") or "main")

    if event_name == "pull_request_target":
        pr = event.get("pull_request") or {}
        if event.get("action") not in {"opened", "reopened"} or (pr.get("user") or {}).get("login") != "dependabot[bot]":
            return None
        number = int(pr["number"])
        url = str(pr["html_url"])
        dependency_title = str(pr.get("title") or "dependency update")
        key = f"dependabot-pr-{number}"
        body = (
            f"Dependabot opened [PR #{number}]({url}): {dependency_title}\n\n"
            "Review the update and its checks. Patch repository compatibility only when a concrete failure or required migration is found. "
            "Open a separate focused PR for the fix and link the Dependabot PR.\n"
        )
        return RepairTask(key, f"Agent review: Dependabot PR #{number}", body, default_branch)

    if event_name == "workflow_run":
        run = event.get("workflow_run") or {}
        if event.get("action") != "completed" or run.get("conclusion") != "failure":
            return None
        if (run.get("actor") or {}).get("login") in {"copilot-swe-agent[bot]", "copilot-swe-agent"}:
            return None
        workflow = str(run["name"])
        run_id = int(run["id"])
        run_url = str(run["html_url"])
        prs = run.get("pull_requests") or []
        pr_number = int(prs[0]["number"]) if prs else None
        scope = f"pr-{pr_number}" if pr_number else str(run.get("head_branch") or default_branch)
        key = f"workflow-{workflow}-{scope}".lower().replace(" ", "-")
        body = (
            f"Workflow [{workflow}]({run_url}) failed (run `{run_id}`, attempt `{run.get('run_attempt', 1)}`).\n\n"
            f"Head branch: `{run.get('head_branch', 'unknown')}`; commit: `{run.get('head_sha', 'unknown')}`.\n"
        )
        if pr_number:
            body += f"Associated PR: #{pr_number}.\n"
        body += "\nReproduce the failing check, identify the cause, and open a focused PR if a repository change fixes it.\n"
        return RepairTask(key, f"Agent repair: {workflow} failed on {scope}", body, default_branch)

    return None


class GitHubAPI:
    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"https://api.github.com{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ubuntu-image-factory-repair-router",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def find_open_issue(self, key: str) -> dict[str, Any] | None:
        marker = f"<!-- repair-router:{key} -->"
        page = 1
        while True:
            path = f"/repos/{self.repository}/issues?state=open&per_page=100&page={page}"
            items = self.request("GET", path)
            for issue in items:
                if "pull_request" not in issue and marker in (issue.get("body") or ""):
                    return issue
            if len(items) < 100:
                return None
            page += 1

    def create_issue(self, task: RepairTask) -> dict[str, Any]:
        payload = {"title": task.title, "body": f"{task.body}\n<!-- repair-router:{task.key} -->\n"}
        return self.request("POST", f"/repos/{self.repository}/issues", payload)

    def assign_agent(self, issue_number: int, base_branch: str) -> None:
        payload = {
            "assignees": [COPILOT_LOGIN],
            "agent_assignment": {
                "target_repo": self.repository,
                "base_branch": base_branch,
                "custom_agent": AGENT_ID,
                "custom_instructions": "Follow AGENTS.md; reproduce and patch only the issue's concrete failure. Open a reviewable PR when a fix is justified.",
            },
        }
        self.request("POST", f"/repos/{self.repository}/issues/{issue_number}/assignees", payload)


def route(event_name: str, event: dict[str, Any], repository: str, issue_token: str, agent_token: str) -> str:
    task = task_from_event(event_name, event, repository)
    if task is None:
        return "event ignored"
    if not issue_token:
        raise ValueError("GITHUB_TOKEN is required to create a repair issue")
    api = GitHubAPI(repository, issue_token)
    issue = api.find_open_issue(task.key)
    if issue is None:
        issue = api.create_issue(task)
    number = int(issue["number"])
    if any(assignee.get("login") == COPILOT_LOGIN for assignee in issue.get("assignees", [])):
        return f"issue #{number} already assigned to Copilot"
    if not agent_token:
        raise RuntimeError(f"issue #{number} remains open: COPILOT_ASSIGNMENT_TOKEN is missing")
    GitHubAPI(repository, agent_token).assign_agent(number, task.base_branch)
    return f"issue #{number} assigned to {AGENT_ID}"


def main() -> int:
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    event = json.loads(event_path.read_text(encoding="utf-8"))
    try:
        result = route(
            os.environ["GITHUB_EVENT_NAME"],
            event,
            os.environ["GITHUB_REPOSITORY"],
            os.environ.get("COPILOT_ASSIGNMENT_TOKEN") or os.environ.get("GITHUB_TOKEN", ""),
            os.environ.get("COPILOT_ASSIGNMENT_TOKEN", ""),
        )
    except (KeyError, ValueError, RuntimeError, urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"repair routing failed: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
