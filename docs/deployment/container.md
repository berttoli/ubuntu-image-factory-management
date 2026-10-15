# OCI deployment

```bash
make build-container RELEASE=26.04 ARCH=amd64
IMAGE_TAG=ghcr.io/ORG/ubuntu-image-factory:26.04-amd64 \
  PUBLISH=1 IMAGE_NAME=ghcr.io/ORG/ubuntu-image-factory:26.04-amd64 \
  make build-container
```

The image is intentionally not a host image: it contains no SSH daemon, no systemd, and no host firewall. Run it with a workload-specific command and retain the non-root default. Publish and deploy by digest, not a mutable channel tag.

