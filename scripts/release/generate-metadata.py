#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--type", required=True, choices=("qcow2", "raw", "iso", "oci"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.artifact.exists():
        raise SystemExit(f"artifact not found: {args.artifact}")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = os.environ.get("GITHUB_SHA", "unknown")
    metadata = {
        "schema_version": 1,
        "artifact": args.artifact.name,
        "artifact_type": args.type,
        "release": args.release,
        "architecture": args.architecture,
        "sha256": sha256(args.artifact),
        "size_bytes": args.artifact.stat().st_size,
        "source_commit": commit,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "builder_os": platform.platform(),
        "builder_architecture": platform.machine(),
        "ubuntu_base_or_iso": os.environ.get("UBUNTU_BASE_OR_ISO", "recorded-by-build-step"),
        "security_scan_status": os.environ.get("SECURITY_SCAN_STATUS", "not-run"),
        "provenance": os.environ.get("PROVENANCE_URI", "pending-release-signing"),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.artifact.with_name(args.artifact.name + ".sha256").write_text(f"{metadata['sha256']}  {args.artifact.name}\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
