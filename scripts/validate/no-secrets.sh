#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if ! command -v rg >/dev/null 2>&1; then
  echo "NOTICE: rg not installed; using the Ruby standard-library secret scanner"
  exec ruby "$ROOT_DIR/scripts/validate/no-secrets.rb"
fi

if rg -n --hidden --glob '!.git/**' --glob '!IMPLEMENTATION_STATUS.md' \
  '(BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|AKIA[0-9A-Z]{16})' .; then
  echo "ERROR: possible secret or reusable credential detected" >&2
  exit 1
fi
if rg --pcre2 -n --hidden --glob '!.git/**' --glob '!IMPLEMENTATION_STATUS.md' \
  'password\s*:\s*(?![\x27"]?(?:__PASSWORD_HASH__|\$\{\{[^}]+\}\})[\x27"]?\s*$)[^\s]+' .; then
  echo "ERROR: possible literal password detected" >&2
  exit 1
fi
echo "secret-pattern scan passed"
