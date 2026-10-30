#!/usr/bin/env python3
"""Turn Ubuntu OVAL feed digests into an actionable review note."""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys


FEEDS = {"noble": "24.04", "resolute": "26.04"}
SUM_LINE = re.compile(r"^([a-f0-9]{64})\s+\*?(.+\.oval\.xml\.bz2)$")


def render(checksums: str, changed: bool, vm_requested: bool = False) -> str:
    if vm_requested and not changed:
        raise ValueError("VM rebuild cannot be requested when the feed is unchanged")
    found: dict[str, str] = {}
    for line in checksums.splitlines():
        match = SUM_LINE.fullmatch(line.strip())
        if not match:
            raise ValueError(f"invalid SHA256SUMS line: {line!r}")
        digest, filename = match.groups()
        codename = next((name for name in FEEDS if Path(filename).name == f"{name}.oval.xml.bz2"), None)
        if codename is None or codename in found:
            raise ValueError(f"unexpected or duplicate OVAL feed: {filename}")
        found[codename] = digest
    if set(found) != set(FEEDS):
        raise ValueError(f"missing OVAL feed(s): {', '.join(sorted(set(FEEDS) - set(found)))}")

    lines = ["## Ubuntu OVAL feed evidence", ""]
    for codename, release in FEEDS.items():
        lines.append(
            f"- Ubuntu {release} ({codename}): `{found[codename]}` "
            f"([Canonical feed](https://security-metadata.canonical.com/oval/com.ubuntu.{codename}.cve.oval.xml.bz2))"
        )
    if not changed:
        rebuild_status = "Feed digest was already seen; this refresh did not dispatch candidate rebuilds."
    elif vm_requested:
        rebuild_status = "Candidate VM (amd64) and container (amd64/arm64) rebuilds were requested for both releases."
    else:
        rebuild_status = (
            "Container candidate rebuilds were requested for both releases; VM rebuilds were deferred because "
            "required AUTOINSTALL repository secrets are missing. Configure those secrets and run build-vm for each release."
        )
    lines.extend(
        [
            "",
            "An unseen feed digest (including the monitor's first observation) calls for review; it does not establish that an image is vulnerable.",
            "",
            rebuild_status,
            "Review the candidate build runs, vulnerability reports, SBOMs, and boot tests before promoting artifacts. "
            "Keep this issue open until those checks and any required remediation are recorded.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: security_report.py SHA256SUMS REPORT.md")
    source, output = map(Path, sys.argv[1:])
    changed = os.environ.get("FEED_CHANGED") == "true"
    vm_requested = os.environ.get("VM_REBUILD_REQUESTED") == "true"
    output.write_text(render(source.read_text(encoding="utf-8"), changed, vm_requested), encoding="utf-8")


if __name__ == "__main__":
    main()
