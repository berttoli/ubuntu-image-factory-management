#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "uri"

ROOT = File.expand_path("../..", __dir__)
FACTORY_PATH = File.join(ROOT, "configs", "factory.yaml")
BASELINE_PATH = File.join(ROOT, "configs", "security", "baseline.yaml")

def fail_with(message)
  warn "CONFIG ERROR: #{message}"
  exit 1
end

factory = YAML.load_file(FACTORY_PATH)
baseline = YAML.load_file(BASELINE_PATH)
fail_with("factory must be a mapping") unless factory.is_a?(Hash)
fail_with("unsupported schema_version") unless factory["schema_version"] == 1

supported = factory.dig("ubuntu", "supported_releases")
fail_with("ubuntu.supported_releases is empty") unless supported.is_a?(Hash) && !supported.empty?
default_release = factory.dig("factory", "default_release")
fail_with("default release is not supported") unless supported.key?(default_release)

supported.each do |release, config|
  fail_with("release #{release} must use YY.04 format") unless release.match?(/^\d{2}\.04$/)
  %w[codename point_release architectures server_iso_base server_iso_base_arm64 server_iso_checksum_url server_iso_checksum_url_arm64].each do |key|
    fail_with("release #{release} missing #{key}") unless config.key?(key)
  end
  config["architectures"].each do |arch|
    fail_with("release #{release} lists unsupported architecture #{arch}") unless factory["architectures"].key?(arch)
  end
  %w[server_iso_base server_iso_base_arm64 server_iso_checksum_url server_iso_checksum_url_arm64].each do |key|
    begin
      URI.parse(config[key])
    rescue URI::InvalidURIError
      fail_with("release #{release} has invalid URL in #{key}")
    end
  end
end

channels = factory.dig("factory", "channels")
fail_with("channels must include stable") unless channels.is_a?(Array) && channels.include?("stable")

rules = baseline["rules"]
fail_with("security baseline has no rules") unless rules.is_a?(Hash) && !rules.empty?
rules.each do |name, rule|
  fail_with("security rule #{name} has no rationale") if rule["rationale"].to_s.strip.empty?
  fail_with("security rule #{name} has no validation reference") if rule["validation"].to_s.strip.empty?
end

puts "configuration valid: #{supported.keys.join(', ')}; default=#{default_release}"
