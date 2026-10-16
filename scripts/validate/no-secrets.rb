#!/usr/bin/env ruby

require "find"

root = File.expand_path("../..", __dir__)
findings = []
private_key_pattern = /(BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|AKIA[0-9A-Z]{16})/
password_pattern = /password\s*:\s*(.+)/
placeholder_pattern = /\A['"]?(?:__PASSWORD_HASH__|\$\{\{[^}]+\}\})['"]?\z/

Find.find(root) do |path|
  relative = path.delete_prefix("#{root}/")
  if relative == ".git" || relative.start_with?(".git/") || relative == "IMPLEMENTATION_STATUS.md"
    Find.prune if File.directory?(path)
    next
  end
  next unless File.file?(path)

  begin
    File.binread(path).each_line.with_index(1) do |line, line_number|
      if line.match?(private_key_pattern)
        findings << "#{relative}:#{line_number}: possible private key or access key"
      end

      password_match = line.match(password_pattern)
      if password_match && !password_match[1].strip.match?(placeholder_pattern)
        findings << "#{relative}:#{line_number}: possible literal password"
      end
    end
  rescue StandardError => e
    warn "unable to scan #{relative}: #{e.message}"
    exit 1
  end
end

unless findings.empty?
  warn findings.join("\n")
  warn "ERROR: possible secret or reusable credential detected"
  exit 1
end

puts "secret-pattern scan passed"
