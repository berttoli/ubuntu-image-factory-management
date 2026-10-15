# Security policy

## Reporting

Do not open a public issue for a suspected vulnerability in this factory or a published image. Use the repository's private security advisory process or contact the maintainers listed in `CODEOWNERS`.

Include the affected commit/tag, target and architecture, reproduction steps, impact, and whether a deployed host or published artifact is involved.

## Scope and gates

The factory treats critical vulnerabilities with an available Ubuntu fix as release-blocking. High vulnerabilities require triage and an expiring, documented exception. Scanner outages and missing feeds are failures, not exceptions. The policy does not claim CIS certification.

Published artifacts include checksums, SBOM, provenance, a security report, and a Cosign signature when the release workflow is authorized to publish.

## Host maintenance

Building a new image does not patch deployed machines. Deployed hosts must retain unattended security updates and an operational reboot process. Containers must be rebuilt and redeployed when their base image or dependency inventory changes.

