#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
files = sorted(p for p in args.input.rglob("*") if p.is_file() and p.name != "manifest.json")
items = []
for path in files:
    items.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size})
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({"schema_version": 1, "artifacts": items}, indent=2) + "\n")
print(args.output)

