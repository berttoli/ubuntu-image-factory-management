#!/usr/bin/env ruby

require "digest"
require "fileutils"
require "json"
require "net/http"
require "optparse"
require "time"
require "uri"
require "yaml"

ROOT = File.expand_path("../..", __dir__)
USER_AGENT = "ubuntu-image-factory-management/upstream-monitor"

begin
options = {
  output: File.join(ROOT, "artifacts/upstream/report.json"),
  state: File.join(ROOT, "artifacts/upstream/state.sha256")
}

OptionParser.new do |parser|
  parser.banner = "Usage: check_upstream.rb [options]"
  parser.on("--output PATH", "Write the JSON report to PATH") { |path| options[:output] = path }
  parser.on("--state PATH", "Write the stable metadata digest to PATH") { |path| options[:state] = path }
end.parse!

def fetch(url)
  uri = URI(url)
  request = Net::HTTP::Get.new(uri)
  request["User-Agent"] = USER_AGENT
  response = Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == "https", open_timeout: 20, read_timeout: 60) do |http|
    http.request(request)
  end
  unless response.is_a?(Net::HTTPSuccess)
    raise "#{url} returned HTTP #{response.code}"
  end

  response.body
end

def write_file(path, content)
  FileUtils.mkdir_p(File.dirname(path))
  File.write(path, content)
end

config = YAML.safe_load(File.read(File.join(ROOT, "configs/factory.yaml")), aliases: true)
releases = config.fetch("ubuntu").fetch("supported_releases")
report = {
  "schema_version" => 1,
  "checked_at" => Time.now.utc.iso8601,
  "releases" => [],
  "runner_labels" => []
}

releases.each do |release, release_config|
  release_config.fetch("architectures").each do |architecture|
    checksum_url_key = architecture == "arm64" ? "server_iso_checksum_url_arm64" : "server_iso_checksum_url"
    base_url_key = architecture == "arm64" ? "server_iso_base_arm64" : "server_iso_base"
    filename = "ubuntu-#{release_config.fetch('point_release')}-live-server-#{architecture}.iso"
    checksum_url = release_config.fetch(checksum_url_key)
    checksum_manifest = fetch(checksum_url)
    match = checksum_manifest.lines.map do |line|
      line.match(/^([a-f0-9]{64})\s+\*?#{Regexp.escape(filename)}\s*$/i)
    end.compact.first
    raise "#{filename} is missing from #{checksum_url}" unless match

    report["releases"] << {
      "release" => release,
      "architecture" => architecture,
      "iso_url" => "#{release_config.fetch(base_url_key)}/#{filename}",
      "checksum_url" => checksum_url,
      "sha256" => match[1].downcase
    }
  end
end

runner_readme = fetch("https://raw.githubusercontent.com/actions/runner-images/main/README.md")
runner_labels = Dir[File.join(ROOT, ".github/workflows/*.{yml,yaml}")].flat_map do |workflow|
  File.read(workflow).scan(/^\s+runs-on:\s*([^\s#]+)\s*$/).flatten
end.uniq.sort

runner_labels.each do |label|
  report["runner_labels"] << {
    "label" => label,
    "present_in_runner_images" => runner_readme.include?(label)
  }
end
missing_labels = report["runner_labels"].reject { |entry| entry["present_in_runner_images"] }
raise "runner label(s) missing from actions/runner-images README: #{missing_labels.map { |entry| entry['label'] }.join(', ')}" unless missing_labels.empty?

stable_report = report.reject { |key, _value| key == "checked_at" }
state_digest = Digest::SHA256.hexdigest(JSON.generate(stable_report))
write_file(options[:output], JSON.pretty_generate(report) + "\n")
write_file(options[:state], "#{state_digest}\n")

summary = <<~MARKDOWN
  # Upstream metadata report

  Checked at: `#{report['checked_at']}`

  ## Ubuntu release media

  #{report['releases'].map { |entry| "- Ubuntu #{entry['release']} #{entry['architecture']}: `#{entry['sha256']}` ([ISO](#{entry['iso_url']}), [checksums](#{entry['checksum_url']}))" }.join("\n  ")}

  ## GitHub Actions runner labels

  #{report['runner_labels'].map { |entry| "- `#{entry['label']}`: available" }.join("\n  ")}

  Stable metadata digest: `#{state_digest}`
MARKDOWN
write_file(options[:output].sub(/\.json\z/, ".md"), summary)
puts "Upstream metadata validated; stable digest #{state_digest}"
rescue StandardError => e
  warn "upstream metadata validation failed: #{e.message}"
  exit 1
end
