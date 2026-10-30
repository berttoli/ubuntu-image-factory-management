"""Monitor issue updates must preserve reviewer notes and report real feed state."""

import unittest
from unittest.mock import patch

from scripts.monitor import reconcile_issue, security_report


class MonitorIssueTests(unittest.TestCase):
    def test_existing_issue_is_refreshed_without_losing_human_notes(self) -> None:
        existing = "Reviewer note: check point release.\n"
        first = reconcile_issue.merge_body(existing, "Digest: aaa")
        second = reconcile_issue.merge_body(first, "Digest: bbb")
        self.assertIn("Reviewer note: check point release.", second)
        self.assertNotIn("Digest: aaa", second)
        self.assertEqual(second.count(reconcile_issue.START), 1)
        self.assertEqual(second, reconcile_issue.merge_body(second, "Digest: bbb"))

    def test_reconcile_updates_matching_open_issue(self) -> None:
        existing = {"number": 7, "title": "Ubuntu security feed changed", "body": "Human review note"}
        with patch.object(reconcile_issue, "request_json", side_effect=[[existing], {"number": 7}]) as request:
            result = reconcile_issue.reconcile("owner/repo", existing["title"], "New feed evidence", "test-token")
        self.assertEqual(result, "updated issue #7")
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args.args[2], "PATCH")
        self.assertIn("Human review note", request.call_args.args[3]["body"])
        self.assertIn("New feed evidence", request.call_args.args[3]["body"])

    def test_reconcile_creates_issue_if_no_match(self) -> None:
        with patch.object(reconcile_issue, "request_json", side_effect=[[], {"number": 6}]) as request:
            result = reconcile_issue.reconcile("owner/repo", "Upstream image metadata review", "Current ISOs", "test-token")
        self.assertEqual(result, "created issue #6")
        self.assertEqual(request.call_args.args[2], "POST")

    def test_security_report_rejects_missing_feed(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing OVAL feed"):
            security_report.render("a" * 64 + "  noble.oval.xml.bz2\n", changed=True)

    def test_security_report_distinguishes_refresh_from_rebuild(self) -> None:
        checksums = (
            "a" * 64 + "  artifacts/security-monitor/noble.oval.xml.bz2\n"
            + "b" * 64 + "  artifacts/security-monitor/resolute.oval.xml.bz2\n"
        )
        changed = security_report.render(checksums, changed=True, vm_requested=True)
        blocked = security_report.render(checksums, changed=True, vm_requested=False)
        refreshed = security_report.render(checksums, changed=False)
        self.assertIn("Ubuntu 24.04 (noble)", changed)
        self.assertIn("Ubuntu 26.04 (resolute)", changed)
        self.assertIn("VM (amd64) and container", changed)
        self.assertIn("VM rebuilds were deferred", blocked)
        self.assertIn("did not dispatch candidate rebuilds", refreshed)
        with self.assertRaisesRegex(ValueError, "feed is unchanged"):
            security_report.render(checksums, changed=False, vm_requested=True)


if __name__ == "__main__":
    unittest.main()
