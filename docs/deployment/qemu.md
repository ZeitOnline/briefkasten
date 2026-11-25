# Testing with QEMU in a container

`deployment/qemu/` contains a container image that runs a FreeBSD virtual machine via [QEMU](https://www.qemu.org). It serves as a *target host* for trying out the deployment on machines where VirtualBox is not an option, and requires nothing but a container runtime such as Docker.

The virtual machine is started from the official FreeBSD arm64 VM image, which is downloaded and verified against its checksum on first start. It runs under software emulation and has been tested on arm64 hosts.

## Differences to a regular installation

- The virtual machine runs FreeBSD for arm64, whereas the regular installation targets amd64. Packages are installed from the arm64 repository.
- The virtual machine is not installed via mfsBSD, so `make bootstrap` is not part of this setup. The steps that bootstrapping usually takes care of (installing the SSH key, installing Python and enabling `pf`) happen on the first boot of the virtual machine instead.
- Software emulation is slow. A complete run takes about an hour: the first boot around ten minutes including a reboot after installing updates, `make configure-host` and `make start-jails` around ten minutes each and `make configure-jails` around twenty.

## Starting the virtual machine

All commands are run inside `deployment`, with the virtual environment of the deployment tools being active. The SSH public key is expected in `etc/authorized_keys`, as for any other setup.

```
$ docker build -t briefkasten-qemu qemu/
$ docker run -d --name briefkasten-qemu \
    -p 127.0.0.1:47022:22 -p 127.0.0.1:47023:443 \
    -v briefkasten-qemu:/vm \
    -v "$PWD/etc/authorized_keys:/authorized_keys:ro" \
    briefkasten-qemu
```

The console of the virtual machine is available via `docker logs -f briefkasten-qemu`. On its first boot the virtual machine installs updates and reboots once; it is ready as soon as the login prompt appears for the second time.

The following environment variables can be passed to `docker run`:

| Variable | Default | Meaning |
|---|---|---|
| `FREEBSD_RELEASE` | `15.1` | the FreeBSD release of the VM image, which needs to match `ezjail-install-release` in `base.conf` |
| `QEMU_CPUS` | `4` | number of virtual CPUs |
| `QEMU_MEMORY` | `4G` | amount of memory |
| `QEMU_SYSTEM_DISK` | `30G` | size of the system disk |
| `QEMU_DATA_DISK` | `20G` | size of the disk for the `tank` pool |

## Configuration

`etc.sample/qemu.conf` contains a configuration for this setup:

```
$ cp etc.sample/qemu.conf etc/ploy.conf
```

It points to the forwarded SSH port on `127.0.0.1`, uses the second disk of the virtual machine (`vtbd1`) for the data pool and `vtnet0` as the network interface. Its `local_theme_path` assumes that the checkout resides in a directory named `briefkasten`.

The certificate in `etc.sample` uses a 1024 bit key, which the `nginx` of current FreeBSD releases rejects. A suitable self-signed certificate can be created like so:

```
$ openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=briefkasten.qemu" \
    -keyout etc/briefkasten.key -out etc/briefkasten.crt
```

## Installation

With the virtual machine running, the installation continues after the bootstrapping step:

```
$ make configure-host
$ make start-jails
$ make configure-jails
```

Afterwards the briefkasten is available at [https://localhost:47023/briefkasten/](https://localhost:47023/briefkasten/).

## Removing the virtual machine

```
$ docker rm -f briefkasten-qemu
$ docker volume rm briefkasten-qemu
```

The volume contains the downloaded VM image and the disks of the virtual machine. Removing only the container keeps the state of the virtual machine for the next start.
