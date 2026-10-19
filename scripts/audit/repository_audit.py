#!/usr/bin/env python3
"""Produce machine-readable evidence for the repository baseline."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class CommandEvidence:
    command: tuple[str, ...]
    status: str
    exit_code: int | None
    output_tail: str


REQUIRED_PATHS: tuple[str, ...] = (
    "AGENTS.md",
    "CLAUDE.md",
    "configs/factory.yaml",
    "configs/security/baseline.yaml",
    "schemas/factory.schema.json",
    "packer/ubuntu.pkr.hcl",
    "containers/Dockerfile",
    "autoinstall/templates/user-data.yaml.tmpl",
    "tests",
    "docs/architecture/overview.md",
    "docs/architecture/adr/0001-evidence-before-artifact-expansion.md",
    "docs/security/baseline.md",
    "IMPLEMENTATION_STATUS.md",
)

REQUIRED_WORKFLOWS: tuple[str, ...] = (
    "validate.yml",
    "upstream-monitor.yml",
    "security-monitor.yml",
    "build-baremetal.yml",
    "build-vm.yml",
    "build-container.yml",
    "test-images.yml",
    "release.yml",
    "dependency-maintenance.yml",
    "agent-repair-router.yml",
    "claude-repair.yml",
)

REQUIRED_TARGETS: tuple[str, ...] = (
    "help",
    "preflight",
    "validate",
    "test",
    "security",
    "build-vm",
    "build-iso",
    "build-container",
    "test-vm",
    "verify-release",
    "audit",
)

TOOLS: tuple[str, ...] = (
    "bash",
    "ruby",
    "python3",
    "curl",
    "sha256sum",
    "rg",
    "packer",
    "qemu-img",
    "xorriso",
    "docker",
    "syft",
    "trivy",
    "cosign",
    "actionlint",
    "shellcheck",
    "yamllint",
)


def extract_release_tracks(config_text: str) -> list[str]:
    """Extract release keys from the central YAML without requiring PyYAML."""

    return sorted(set(re.findall(r'^\s+"(\d{2}\.04)":\s*$', config_text, re.MULTILINE)))


def extract_make_targets(makefile_text: str) -> set[str]:
    """Return explicitly declared Make targets."""

    return set(re.findall(r"^([A-Za-z0-9][A-Za-z0-9_-]*):(?:\s|$)", makefile_text, re.MULTILINE))


def check_paths(root: Path, paths: Iterable[str]) -> list[Check]:
    return [
        Check(
            name=f"path:{path}",
            status="pass" if (root / path).exists() else "fail",
            detail="present" if (root / path).exists() else "missing",
        )
        for path in paths
    ]


def find_identity_placeholders(root: Path) -> list[str]:
    """Find template ownership identities that must not survive into a fork."""

    findings: list[str] = []
    placeholder_tokens = (
        "OWNER" + "_OR_TEAM",
        "https://github.com/" + "OWNER/",
        "your_" + "username",
        "some" + "name",
    )
    pattern = re.compile("|".join(re.escape(token) for token in placeholder_tokens))
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "artifacts" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(text):
            findings.append(str(path.relative_to(root)))
    return findings


def run_command(root: Path, command: Sequence[str], timeout_seconds: int = 300) -> CommandEvidence:
    try:
        completed = subprocess.run(
            list(command),
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or "")[-4000:]
        return CommandEvidence(tuple(command), "fail", None, f"timed out\n{output}")
    output = completed.stdout[-4000:]
    return CommandEvidence(tuple(command), "pass" if completed.returncode == 0 else "fail", completed.returncode, output)


def git_value(root: Path, args: Sequence[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build_report(root: Path, run_gates: bool) -> dict[str, object]:
    config_text = (root / "configs/factory.yaml").read_text(encoding="utf-8")
    makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    workflows_dir = root / ".github/workflows"
    checks = check_paths(root, REQUIRED_PATHS)
    checks.extend(
        Check(
            name=f"workflow:{workflow}",
            status="pass" if (workflows_dir / workflow).is_file() else "fail",
            detail="present" if (workflows_dir / workflow).is_file() else "missing",
        )
        for workflow in REQUIRED_WORKFLOWS
    )

    tracks = extract_release_tracks(config_text)
    checks.append(Check("release-tracks", "pass" if tracks == ["24.04", "26.04"] else "fail", ", ".join(tracks)))
    targets = extract_make_targets(makefile_text)
    missing_targets = sorted(set(REQUIRED_TARGETS) - targets)
    checks.append(Check("make-targets", "pass" if not missing_targets else "fail", "all required targets present" if not missing_targets else f"missing: {', '.join(missing_targets)}"))

    policy_text = (root / "configs/security/baseline.yaml").read_text(encoding="utf-8")
    required_policy_markers = ("PermitRootLogin", "PasswordAuthentication", "default_incoming", "security_origins_only", "sshd: false")
    missing_policy = [marker for marker in required_policy_markers if marker not in policy_text]
    checks.append(Check("security-policy-markers", "pass" if not missing_policy else "fail", "required controls present" if not missing_policy else f"missing: {', '.join(missing_policy)}"))
    identity_placeholders = find_identity_placeholders(root)
    checks.append(Check("fork-identity", "pass" if not identity_placeholders else "fail", "repository identities are concrete" if not identity_placeholders else f"placeholders: {', '.join(identity_placeholders)}"))

    tools = {tool: shutil.which(tool) for tool in TOOLS}
    gates: list[CommandEvidence] = []
    if run_gates:
        gates = [run_command(root, ("make", "validate")), run_command(root, ("make", "test"))]

    failed_checks = sum(check.status == "fail" for check in checks)
    failed_gates = sum(gate.status == "fail" for gate in gates)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": {"commit": git_value(root, ["rev-parse", "HEAD"]), "branch": git_value(root, ["branch", "--show-current"])},
        "summary": {"status": "pass" if failed_checks == 0 and failed_gates == 0 else "fail", "failed_checks": failed_checks, "failed_gates": failed_gates},
        "checks": [asdict(check) for check in checks],
        "gates": [asdict(gate) for gate in gates],
        "tools": tools,
    }


def markdown_report(report: dict[str, object]) -> str:
    summary = report["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# Repository audit evidence",
        "",
        f"Status: **{summary['status']}**",
        f"Commit: `{report['git']['commit']}`",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Structural checks",
        "",
    ]
    for check in report["checks"]:
        lines.append(f"- {check['status'].upper()}: `{check['name']}` — {check['detail']}")
    lines.extend(["", "## Executed gates", ""])
    for gate in report["gates"]:
        lines.append(f"- {gate['status'].upper()}: `{' '.join(gate['command'])}` (exit {gate['exit_code']})")
    lines.extend(["", "## Tool availability", ""])
    for tool, path in report["tools"].items():
        lines.append(f"- `{tool}`: `{path or 'not found'}`")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/audit/portfolio-audit.json")
    parser.add_argument("--skip-gates", action="store_true", help="Only run structural checks")
    args = parser.parse_args(argv)
    report = build_report(ROOT, run_gates=not args.skip_gates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown_report(report), encoding="utf-8")
    print(f"audit {report['summary']['status']}: {args.output}")
    return 0 if report["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
