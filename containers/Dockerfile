ARG UBUNTU_RELEASE=26.04
FROM ubuntu:${UBUNTU_RELEASE}

ARG UBUNTU_RELEASE
LABEL org.opencontainers.image.title="Ubuntu Image Factory minimal runtime" \
      org.opencontainers.image.description="Minimal Ubuntu base with no SSH or init system" \
      org.opencontainers.image.source="https://github.com/OWNER/ubuntu-image-factory" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="ubuntu:${UBUNTU_RELEASE}"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home --home-dir /home/factory --shell /usr/sbin/nologin factory \
    && chmod 0750 /home/factory

USER factory
WORKDIR /home/factory
CMD ["/usr/bin/env"]

