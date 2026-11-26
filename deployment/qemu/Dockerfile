FROM debian:trixie-slim
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ca-certificates curl genisoimage qemu-efi-aarch64 qemu-system-arm qemu-utils xz-utils \
    && rm -rf /var/lib/apt/lists/*
COPY start.sh /start.sh
VOLUME /vm
EXPOSE 22 80 443
ENTRYPOINT ["/start.sh"]
