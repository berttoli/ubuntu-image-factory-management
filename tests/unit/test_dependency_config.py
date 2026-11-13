"""Keep Dependabot's pip target connected to the validators CI installs."""

import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict:
    result = subprocess.run(
        ["ruby", "-rjson", "-ryaml", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]))", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class DependencyConfigTests(unittest.TestCase):
    def test_dependabot_tracks_the_ci_validator_manifest(self) -> None:
        config = load_yaml(ROOT / ".github/dependabot.yml")
        pip_updates = [update for update in config["updates"] if update["package-ecosystem"] == "pip"]
        self.assertEqual(len(pip_updates), 1)
        manifest = ROOT / pip_updates[0]["directory"].lstrip("/") / "requirements.txt"
        self.assertTrue(manifest.is_file(), "Dependabot's pip target needs a requirements.txt manifest")

        pins = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.fullmatch(r"([a-zA-Z0-9_-]+)==([0-9]+(?:\.[0-9]+)+)", line)
            self.assertIsNotNone(match, f"Validator must have a reviewable version pin: {line}")
            assert match is not None
            pins[match[1]] = match[2]
        self.assertTrue({"yamllint", "ansible-lint"}.issubset(pins))

        workflow = load_yaml(ROOT / ".github/workflows/validate.yml")
        installs = [step.get("run", "") for step in workflow["jobs"]["validate"]["steps"]]
        self.assertTrue(
            any(re.search(r"python3 -m pip install[^\n]* -r " + re.escape(str(manifest.relative_to(ROOT))) + r"(?:\s|$)", script)
                for script in installs),
            "CI must install the manifest monitored by Dependabot",
        )


if __name__ == "__main__":
    unittest.main()
