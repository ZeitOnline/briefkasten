#!/bin/sh
set -e

RELEASE="${FREEBSD_RELEASE:-15.1}"
IMAGE="FreeBSD-${RELEASE}-RELEASE-arm64-aarch64-BASIC-CLOUDINIT-zfs.qcow2"
URL="https://download.freebsd.org/releases/VM-IMAGES/${RELEASE}-RELEASE/aarch64/Latest"

cd /vm
if [ ! -f base.qcow2 ]; then
    curl -fsSL -o "${IMAGE}.xz" "${URL}/${IMAGE}.xz"
    curl -fsSL "${URL}/CHECKSUM.SHA256" \
        | awk -v f="${IMAGE}.xz" '$2 == "(" f ")" { print $NF "  " f }' \
        | sha256sum -c -
    xz -d "${IMAGE}.xz"
    mv "${IMAGE}" base.qcow2
fi
if [ ! -f system.qcow2 ]; then
    qemu-img create -q -f qcow2 -b base.qcow2 -F qcow2 system.qcow2 "${QEMU_SYSTEM_DISK:-30G}"
    qemu-img create -q -f qcow2 data.qcow2 "${QEMU_DATA_DISK:-20G}"
    cp /usr/share/AAVMF/AAVMF_VARS.fd vars.fd
fi

SEED=$(mktemp -d)
printf 'instance-id: briefkasten-qemu\nlocal-hostname: briefkasten\n' > "${SEED}/meta-data"
KEYS=$(grep -v -e '^#' -e '^$' /authorized_keys \
    | sed 's|.*|  - echo "&" >> /root/.ssh/authorized_keys|')
cat > "${SEED}/user-data" <<EOF
#cloud-config
runcmd:
  - mkdir -p -m 700 /root/.ssh
  - install -m 600 /dev/null /root/.ssh/authorized_keys
${KEYS}
  - echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config
  - env ASSUME_ALWAYS_YES=yes pkg bootstrap -f
  - env PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin pkg install -y python3
  - echo "pass all" > /etc/pf.conf
  - sysrc pf_enable=YES sshd_enable=YES
  - service pf start
  - service sshd restart
EOF
genisoimage -quiet -output /vm/seed.iso -volid cidata -joliet -rock \
    "${SEED}/user-data" "${SEED}/meta-data"

exec qemu-system-aarch64 \
    -machine virt -cpu max -accel tcg,thread=multi \
    -smp "${QEMU_CPUS:-4}" -m "${QEMU_MEMORY:-4G}" \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/AAVMF/AAVMF_CODE.fd \
    -drive if=pflash,format=raw,file=/vm/vars.fd \
    -drive if=virtio,format=qcow2,file=/vm/system.qcow2 \
    -drive if=virtio,format=qcow2,file=/vm/data.qcow2 \
    -drive if=virtio,format=raw,readonly=on,file=/vm/seed.iso \
    -netdev user,id=net0,hostfwd=tcp:0.0.0.0:22-:22,hostfwd=tcp:0.0.0.0:80-:80,hostfwd=tcp:0.0.0.0:443-:443 \
    -device virtio-net-pci,netdev=net0,romfile= \
    -nographic -serial mon:stdio
