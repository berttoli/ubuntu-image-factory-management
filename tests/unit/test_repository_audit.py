import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.audit.repository_audit import extract_make_targets, extract_release_tracks, find_identity_placeholders


ROOT = Path(__file__).resolve().parents[2]


class RepositoryAuditTests(unittest.TestCase):
    def test_parsers_cover_release_and_make_contracts(self):
        self.assertEqual(extract_release_tracks('  "26.04":\n  "24.04":\n'), ["24.04", "26.04"])
        self.assertEqual(extract_make_targets("validate:\n\ntest:\n"), {"validate", "test"})

    def test_identity_placeholder_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            placeholder = "OWNER" + "_" + "OR" + "_TEAM"
            (root / "CODEOWNERS").write_text("* @" + placeholder + "\n")
            self.assertEqual(find_identity_placeholders(root), ["CODEOWNERS"])

    def test_structural_audit_emits_passing_machine_readable_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.json"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/audit/repository_audit.py"), "--skip-gates", "--output", str(output)],
                check=True,
            )
            report = json.loads(output.read_text())
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["summary"]["failed_checks"], 0)
            self.assertEqual(report["gates"], [])


if __name__ == "__main__":
    unittest.main()
