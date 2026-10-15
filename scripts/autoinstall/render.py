#!/usr/bin/env python3
"""Render an autoinstall seed without accepting credentials from source files."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or "\n" in value:
        raise SystemExit(f"ERROR: {name} must be provided as a single non-empty value")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--profile", default="minimal", choices=("minimal", "hardened", "encrypted", "custom-hardware"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    password_hash = required_env("AUTOINSTALL_PASSWORD_HASH")
    ssh_key = required_env("AUTOINSTALL_SSH_PUBLIC_KEY")
    disk_serial = required_env("AUTOINSTALL_TARGET_DISK_SERIAL")
    hostname = os.environ.get("AUTOINSTALL_HOSTNAME", f"ubuntu-{args.release.replace('.', '-')}")
    if any(value in ("__PASSWORD_HASH__", "__SSH_PUBLIC_KEY__", "__DISK_SERIAL__") for value in (password_hash, ssh_key, disk_serial)):
        raise SystemExit("ERROR: template placeholders are not valid deployment inputs")

    template = Path(__file__).resolve().parents[2] / "autoinstall" / "templates" / "user-data.yaml.tmpl"
    content = template.read_text(encoding="utf-8")
    replacements = {
        "__RELEASE__": args.release,
        "__ARCH__": args.arch,
        "__PROFILE__": args.profile,
        "__PASSWORD_HASH__": password_hash,
        "__SSH_PUBLIC_KEY__": ssh_key,
        "__DISK_SERIAL__": disk_serial,
        "__HOSTNAME__": hostname,
    }
    for marker, value in replacements.items():
        content = content.replace(marker, value)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "user-data").write_text(content, encoding="utf-8")
    (args.output / "meta-data").write_text(f"instance-id: {hostname}\nlocal-hostname: {hostname}\n", encoding="utf-8")
    print(f"rendered autoinstall seed for {args.release}/{args.arch} profile={args.profile} into {args.output}")


if __name__ == "__main__":
    main()

