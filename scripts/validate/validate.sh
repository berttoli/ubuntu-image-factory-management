#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
"$ROOT_DIR/scripts/validate/yaml.sh"
ruby "$ROOT_DIR/scripts/validate/config.rb"
"$ROOT_DIR/scripts/validate/no-secrets.sh"

if command -v yamllint >/dev/null 2>&1; then
  yamllint -c "$ROOT_DIR/.yamllint.yml" "$ROOT_DIR"
else
  echo "NOTICE: yamllint not installed; YAML style validation deferred to CI"
fi

if command -v packer >/dev/null 2>&1; then
  (cd "$ROOT_DIR/packer" && packer init -upgrade=false . && packer validate -syntax-only .)
else
  echo "NOTICE: packer not installed; Packer syntax validation deferred to CI"
fi
if command -v shellcheck >/dev/null 2>&1; then
  mapfile -t shell_files < <(find "$ROOT_DIR/scripts" -type f -name '*.sh' -print)
  ((${#shell_files[@]} == 0)) || shellcheck "${shell_files[@]}"
else
  echo "NOTICE: shellcheck not installed; shell lint deferred to CI"
fi
echo "validation complete"
