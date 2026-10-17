SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

RELEASE ?= 26.04
ARCH ?= amd64
FORMAT ?= qcow2
PROFILE ?= hardened

.PHONY: help preflight validate test audit security build-vm build-iso build-container test-vm verify-release clean

help:
	@printf '%s\n' \
	  'make preflight                 Check host capabilities and inputs' \
	  'make validate                  Validate YAML, config, secrets, Packer/shell when installed' \
	  'make test                      Run standard-library unit/integration/security tests' \
	  'make audit                     Produce machine-readable baseline evidence' \
	  'make security                  Run mandatory Syft + Trivy security gates' \
	  'make build-vm                  Build QCOW2 or RAW with Packer/QEMU' \
	  'make build-iso                 Build unattended bare-metal ISO on Linux' \
	  'make build-container           Build minimal OCI image with Docker Buildx' \
	  'make test-vm IMAGE=...         Boot-test a generated VM with QEMU' \
	  'make verify-release            Verify checksums in a release manifest'

preflight:
	@RELEASE=$(RELEASE) ARCH=$(ARCH) ./scripts/preflight.sh

validate:
	@./scripts/validate/validate.sh

test:
	@python3 -m unittest discover -s tests -p 'test_*.py' -v

audit:
	@python3 scripts/audit/repository_audit.py

security:
	@ARTIFACT=$(or $(ARTIFACT),build/container) ./scripts/security/scan.sh

build-vm:
	@RELEASE=$(RELEASE) ARCH=$(ARCH) FORMAT=$(FORMAT) PROFILE=$(PROFILE) ./scripts/build/build-vm.sh

build-iso:
	@RELEASE=$(RELEASE) ARCH=$(ARCH) PROFILE=$(PROFILE) ./scripts/build/build-iso.sh

build-container:
	@RELEASE=$(RELEASE) ARCH=$(ARCH) ./scripts/build/build-container.sh

test-vm:
	@ARCH=$(ARCH) ./scripts/test/test-vm.sh $(IMAGE)

verify-release:
	@MANIFEST=$(or $(MANIFEST),artifacts/release/manifest.json) ./scripts/release/verify.sh

clean:
	@rm -rf build artifacts
