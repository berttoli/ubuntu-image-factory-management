#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
release="${RELEASE:-26.04}"
arch="${ARCH:-$(uname -m)}"
[[ "$arch" == x86_64 ]] && arch=amd64
[[ "$arch" == aarch64 ]] && arch=arm64
[[ "$release" == 26.04 || "$release" == 24.04 ]] || { echo "ERROR: unsupported RELEASE=$release" >&2; exit 2; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: docker is required for container builds" >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo "ERROR: Docker CLI is present but the daemon is unavailable; start Docker Desktop or use a Linux runner" >&2; exit 1; }

tag="${IMAGE_TAG:-${IMAGE_NAME:-ubuntu-image-factory:${release}-${arch}}}"
platform="linux/$arch"
if [[ "${PUBLISH:-0}" == 1 ]]; then
  [[ -n "${IMAGE_NAME:-}" ]] || { echo "ERROR: IMAGE_NAME is required when PUBLISH=1" >&2; exit 2; }
  tag="$IMAGE_NAME"
  docker buildx build --platform "$platform" --build-arg UBUNTU_RELEASE="$release" --tag "$tag" --push "$ROOT_DIR/containers"
else
  docker buildx build --platform "$platform" --build-arg UBUNTU_RELEASE="$release" --tag "$tag" --load "$ROOT_DIR/containers"
fi
echo "container image ready: $tag"
