import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ClaudeWorkflowTests(unittest.TestCase):
    def test_router_uses_github_token_and_explicitly_dispatches_claude(self):
        workflow = (ROOT / ".github/workflows/agent-repair-router.yml").read_text(encoding="utf-8")
        router = (ROOT / "scripts/automation/repair_router.py").read_text(encoding="utf-8")
        self.assertIn("contents: write", workflow)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)
        self.assertNotIn("COPILOT_ASSIGNMENT_TOKEN", workflow)
        self.assertIn('"event_type": "claude_repair"', router)

    def test_claude_runs_on_repository_dispatch_with_minimal_required_access(self):
        workflow = (ROOT / ".github/workflows/claude-repair.yml").read_text(encoding="utf-8")
        self.assertIn("repository_dispatch:", workflow)
        self.assertIn("types: [claude_repair]", workflow)
        self.assertRegex(workflow, r"uses: anthropics/claude-code-action@[0-9a-f]{40}(?:\s|$)")
        self.assertIn("secrets.ANTHROPIC_API_KEY", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("draft: true", workflow)
        self.assertIn("branch.startsWith('claude/')", workflow)
        self.assertIn("Check Claude API credential", workflow)
        self.assertIn('if [[ -z "$ANTHROPIC_API_KEY" ]]', workflow)
        self.assertIn("github-token: ${{ github.token }}", workflow)
        self.assertNotIn("github-token: ${{ steps.claude.outputs.github_token }}", workflow)
        self.assertNotIn("pull_request_target:", workflow)


if __name__ == "__main__":
    unittest.main()
