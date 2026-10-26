#!/usr/bin/env python3
"""Create or refresh a monitor issue without overwriting human notes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


START = "<!-- factory-monitor:start -->"
END = "<!-- factory-monitor:end -->"


def merge_body(existing: str, report: str) -> str:
    managed = f"{START}\n{report.strip()}\n{END}"
    if START in existing or END in existing:
        if existing.count(START) != 1 or existing.count(END) != 1:
            raise ValueError("existing issue has malformed monitor markers")
        before, rest = existing.split(START, 1)
        _, after = rest.split(END, 1)
        return before + managed + after
    return f"{existing.rstrip()}\n\n{managed}\n" if existing.strip() else managed + "\n"


def request_json(url: str, token: str, method: str = "GET", payload: dict[str, str] | None = None) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ubuntu-image-factory-monitor",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"GitHub issue request failed: {method} {url}: {error}") from error


def reconcile(repository: str, title: str, report: str, token: str) -> str:
    if not repository or "/" not in repository or not token:
        raise ValueError("repository and GITHUB_TOKEN are required")
    base = f"https://api.github.com/repos/{repository}/issues"
    page = 1
    while True:
        issues = request_json(f"{base}?state=open&per_page=100&page={page}", token)
        matching = [issue for issue in issues if issue.get("title") == title and "pull_request" not in issue]
        if matching:
            issue = matching[0]
            body = merge_body(issue.get("body") or "", report)
            if body != issue.get("body"):
                request_json(f"{base}/{issue['number']}", token, "PATCH", {"body": body})
            return f"updated issue #{issue['number']}"
        if len(issues) < 100:
            break
        page += 1
    created = request_json(base, token, "POST", {"title": title, "body": merge_body("", report)})
    return f"created issue #{created['number']}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        parser.error("GITHUB_TOKEN is required")
    report = args.body_file.read_text(encoding="utf-8").rstrip()
    report += f"\n\nMonitor run: {args.run_url}\n"
    print(reconcile(args.repository, args.title, report, token))


if __name__ == "__main__":
    main()
