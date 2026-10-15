# Release operations

Stable release names use:

```text
ubuntu-<release>-<arch>-<artifact-type>-YYYY.MM.DD
```

The release workflow builds candidate artifacts, runs boot/security checks, generates SBOM and provenance, signs with Cosign keyless OIDC, and creates a GitHub Release. Containers are pushed to GHCR with a digest and a matching signed attestation. The `stable` channel is promoted only by an explicit workflow dispatch or reviewed release event.

Required asset set: artifact, SHA-256 checksum, SBOM, provenance, signature, build metadata, and security report. `scripts/release/verify.sh` verifies checksums locally; Cosign verification additionally requires the release identity and issuer constraints documented in the workflow.

Artifacts are immutable. If a build is superseded, publish a new date/commit-specific release and update a channel manifest; never replace an existing asset at the same URL.

