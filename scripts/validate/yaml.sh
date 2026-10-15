#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

command -v ruby >/dev/null 2>&1 || { echo "ERROR: ruby is required to parse YAML" >&2; exit 1; }
ruby - "$ROOT_DIR" <<'RUBY'
require "yaml"
root = ARGV.fetch(0)
files = (
  Dir.glob(File.join(root, "**", "*.{yml,yaml}"), File::FNM_EXTGLOB) +
  Dir.glob(File.join(root, ".github", "**", "*.{yml,yaml}"), File::FNM_EXTGLOB)
).uniq
errors = []
files.each do |file|
  begin
    YAML.load_file(file)
  rescue StandardError => e
    errors << "#{file}: #{e.message}"
  end
end
abort errors.join("\n") unless errors.empty?
puts "YAML syntax valid: #{files.length} files"
RUBY
