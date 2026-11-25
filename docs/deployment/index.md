# Overview

While we could simply provide pre-built installation images, this would defeat the whole idea of running a trustworthy, open source dropbox in the first place, because then you and your submitters would have to blindly trust these binaries without being able to verify their integrity.

Instead the idea is to use as few pre-built ingredients as possible and acquire them from trusted sources (i.e. from the official FreeBSD repositories). In essence we provide you with a grocery list of ingredients along with a recipe and let you do all the shopping and cooking yourself instead of serving a pre-cooked meal!

An instance of the briefkasten is deployed by running scripts on a *control host* (i.e. your local machine) which then configure and install it on a *target host* (i.e. a virtual machine for development and testing, or dedicated hardware for production).

During this process the *target host* will boot from a FreeBSD installer medium (ISO image or USB stick), then (remotely) receive instructions to install itself with a minimal configuration, boot into that system and then finalize the installation.

The deployment is based on [ploy](https://github.com/ployground/ploy), [bsdploy](https://github.com/ployground/bsdploy) and [Ansible](https://www.ansible.com).

# tl;dr

The short version is:

1. *populate `etc`* with a custom `ploy.conf`, an `authorized_keys` file, some `pgp_pubkeys` and a certificate and key for the webserver `briefkasten.crt` and `briefkasten.key`
2. `uv sync --frozen`
3. `source .venv/bin/activate`
4. *make sure the host is booted into mfsBSD* (if you're using VirtualBox, run `ploy start briefkasten-vbox`)
5. `make bootstrap`
6. `make configure-host`
7. `make start-jails`
8. `make configure-jails`
9. `make upload-pgp-keys`

# Obtaining the sources

You need to clone the entire project onto the *control host* but will then work only inside `deployment` (where this README is located):

```
git clone https://github.com/ZeitOnline/briefkasten.git
cd briefkasten/deployment
```

# Installing the requirements on the control host

The *control host* needs:

- [uv](https://docs.astral.sh/uv/) for installing the deployment tools – it will also take care of installing a suitable Python version (currently Python 3.12) if none is available
- `make` and `rsync`
- the development headers of `liblzma`, which are needed to build one of the dependencies (i.e. `brew install xz` on macOS or `apt install liblzma-dev` on Debian/Ubuntu)
- optionally [VirtualBox](https://www.virtualbox.org) for running a local test instance

Then install the deployment tools (`ploy`, `bsdploy`, `ansible` etc.) into a virtual environment:

```
$ uv sync --frozen
```

and activate it, so that the subsequent commands can find the installed tools without them having to be installed globally:

```
$ source .venv/bin/activate
```

All of the following commands assume that this virtual environment is active.

# Configuring your setup

Before we can continue, we need to configure your setup on the *control host*. The deployment scripts require four assets, all of which need to reside inside `etc`.

In practice it is advisable to keep the entire `etc` under separate version control – it contains everything that distinguishes your particular setup from a generic one. A good start is to copy `etc.sample` to `etc` and perform a `git init` inside it. YMMV.

## ploy.conf – the main configuration file

Create your own configuration directory:

```
$ mkdir etc
```

Create a copy from the provided example:

```
$ cp etc.sample/plain.conf etc/ploy.conf
```

If you want to use VirtualBox to try out the installation on a local virtual machine, you can copy `etc.sample/vbox.conf` instead, which contains a ready-to-use setup.

You will (at least) need to provide values in the `[ez-master:briefkasten]` section for the following keys:

- `ip`
- `fingerprint`

Note that you cannot specify the SSH fingerprint at this time yet, you need to wait until after `make bootstrap` has run (see below).

And in the `[macro:ez-base]` section for these:

- `fqdn` – the hostname under which the webserver is reached
- `approot_url` – the URL path under which the briefkasten is hosted
- `editors` – the email addresses of the recipients of the submissions
- `admins` – the email addresses of the admins, who get notified when a submission fails
- `mail_sender` – the sender address of all emails
- `post_secret` – a secret used to sign the submission URLs (there is deliberately no default value). The same value identifies test submissions by the watchdog (see [Monitoring](monitoring.md)).
- `local_theme_path` and `theme_name` – the theme to use (see [Customization](../application/develop.md#customization))

By default emails are sent via `localhost` on port 25 without authentication. To use another SMTP server, set `mail_host`, `mail_port`, `mail_user` and `mail_password`. Instead of storing the password in plain text, you can also provide it encrypted via `mail_password_file` (see [ploy_ansible's lookup plugins](https://github.com/ployground/ploy_ansible#ansible-lookup-plugins)).

Optionally, you can set `root_email` to forward the system emails of the *target host* to an external address.

`base.conf` contains the defaults for all other settings, i.e. the FreeBSD release to install, the timeout for cleansing attachments or the size threshold above which attachments are archived instead of being sent via email. Look inside the files for details, they should be self explanatory.

## SSH public key

This key (usually `~/.ssh/id_ed25519.pub` or `~/.ssh/id_rsa.pub`) will be installed on the *target host* during bootstrapping and will enable access to it.

You need to place it inside `etc/authorized_keys`.

## Editorial PGP keys

For each email address configured as recipient of the submissions in `ploy.conf` you must provide a matching public PGP key which will be used to encrypt the submissions.

These need to reside inside `etc/pgp_pubkeys/` and are expected to end in `*.gpg`. You can use one key per editor or any public keyring format that is understood by `gnupg`.

## SSL certificate for the webserver

The webserver will be configured to communicate exclusively via HTTPS – to this end you will need to provide a suitable certificate/key pair. It is expected in `etc/briefkasten.crt` and `etc/briefkasten.key` respectively, `etc.sample` contains a self-signed pair for development and testing purposes.

In the most common scenario the public facing HTTP server is not identical with the webserver of this setup (IOW the briefkasten is running behind a proxy and is reachable via a subpath such as `/briefkasten/`). In this case it is entirely reasonable to provide a self-signed key/certificate pair since its only purpose is to ensure that the HTTP traffic between the proxy and the briefkasten is encrypted.

If, however, you wish to expose the briefkasten directly to the public, we provide support for using [Let's Encrypt](https://letsencrypt.org) via the [acme.sh](https://github.com/acmesh-official/acme.sh) client. The certificate is issued using the webroot mode, i.e. the configured `fqdn` must be reachable publicly via HTTP. To use it, set the following in the `ez-base` section of your configuration:

```
use_acme = true
acme_domain = <the name of the nsupdate key>
acme_key = <the secret of the nsupdate key>
acme_ddns_server = <the IP or hostname of the nameserver>
```

The `acme_*` values are written to the nsupdate configuration of acme.sh and need to be defined, although issuing and renewing the certificate in webroot mode does not use them.

The certificate will then be renewed automatically via a cron job.

# Booting the target host into FreeBSD

Next we will need to boot the *target host* into the FreeBSD installer. Since an official vanilla installer from freebsd.org would require quite a bit more manual configuration we instead use a slightly modified version of this called [mfsBSD](https://mfsbsd.vx.sk) – it basically attempts to configure the network via DHCP and has SSH enabled for `root` with a defined password of `mfsroot`.

mfsBSD is only used for bootstrapping, the FreeBSD release that will actually be installed on the *target host* is configured in `base.conf` (`ezjail-install-release` and `bootstrap-bsd-url`). Use the "special edition" (`mfsbsd-se-*`) image of a recent release from the [mfsBSD download page](https://mfsbsd.vx.sk/files/).

## Installation using VirtualBox

This is the recommended way for testing and developing, as it allows for 100% automation. You need [VirtualBox](https://www.virtualbox.org) with the command line tools available in your path.

- `ploy start briefkasten-vbox` – this will download the ISO image, create a virtual machine and boot it from the image
- wait till the login prompt - we're now booted into the mfsBSD installer
- continue with **Bootstrapping the target host**

## Installation using other virtualization software

Download an mfsBSD ISO image along with its checksum file from the [mfsBSD download page](https://mfsbsd.vx.sk/files/) and verify the integrity of the downloaded image (see below). Then create a virtual machine and boot it from that image. At the login prompt log in with username/password `root/mfsroot`. Use `ifconfig` to get the assigned IP address (or assign one manually) and enter it into `ploy.conf`.

- continue with **Bootstrapping the target host**

## Installation on physical hardware

This is the recommended setup for production. The machine doesn't need to be particularly powerful, but it will require at least 2 GB RAM and 10 GB disk space.

Download an mfsBSD image (`*.img`) along with its checksum file (`*.sums.txt`) from the [mfsBSD download page](https://mfsbsd.vx.sk/files/) and verify the integrity of the downloaded image:

```
shasum -a 256 mfsbsd-se-<version>-RELEASE-amd64.img
```

Make sure the output matches the one in the downloaded text file. Next you will need to create a bootable medium from that image.

### Creating a bootable USB medium

On macOS:

- run `diskutil list` to see which drives are currently in your system
- insert your medium
- re-run `diskutil list` and notice which number it has been assigned (N)
- run `diskutil unmountDisk /dev/diskN`
- run `sudo dd if=mfsbsd-se-<version>-RELEASE-amd64.img of=/dev/diskN bs=1m`
- run `diskutil unmountDisk /dev/diskN`

On Linux, identify the device of the USB medium (i.e. via `lsblk`) and write the image using `sudo dd if=mfsbsd-se-<version>-RELEASE-amd64.img of=/dev/sdX bs=1M`.

Insert the USB stick into the *target host* and boot from it. Log in as `root` using the pre-configured password `mfsroot`. Either note the name of the ethernet interface and the IP address it has been given by running `ifconfig` or set them to the desired values in `/etc/rc.conf` if you do not have a DHCP environment.

Run `gpart list` and note the device name of the hard drive(s). Enter these values into your `etc/ploy.conf`.

# Bootstrapping the target host

Either way you now should have the *target host* booted into mfsBSD with a known IP address which has been entered into `etc/ploy.conf` and we can continue.

The functionality of the briefkasten has been split into several jails: a **webserver** jail which only contains the frontend, an **appserver** jail which contains the web application that handles the submissions, a **worker** jail which processes the submissions and sends them to the editors and a number of separate **cleanser** jails that only deal with sanitizing and anonymizing any submitted attachments.

Since we have a running host we can prepare for these jails like so:

- run `make bootstrap` on the *control host*
- answer `y` for the questions coming up. The host will reboot automatically after the script has run.
- at the end of the script run, the script will output the fingerprint it has generated for the SSH daemon on the host. You *must* enter that in the `[ez-master:briefkasten]` section of your `ploy.conf` as `fingerprint =`.
- in the meantime the *target host* has probably finished rebooting. Now run `make configure-host`

Now we have all requirements in place to install the jails.

# Installing the jails

First start and create the (empty) jails `make start-jails`, then configure them: `make configure-jails`.

Finally, you need to upload and install the PGP keys of the editors and admins: `make upload-pgp-keys`.

If `ploy` crashes on macOS with `ERROR! A worker was found in a dead state`, setting the environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` might help. The `make` targets already take care of that.

# Testing the installation

Once all steps have been completed successfully you should be able to visit the briefkasten in a web browser.

In the case of testing via VirtualBox the URL would be [https://localhost:47023/briefkasten/](https://localhost:47023/briefkasten/).

Note, that the above URL will only work for a configuration based on `vbox.conf`, for other setups you must substitute the IP address and port accordingly.

In some cases the URL above does not work on VirtualBox based systems, in that case you need to find out which IP address the VirtualBox instance has received, like so:

```
# ploy ssh briefkasten 'ifconfig em0'
em0: flags=8843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
        options=9b<RXCSUM,TXCSUM,VLAN_MTU,VLAN_HWTAGGING,VLAN_HWCSUM>
        ether 08:00:27:02:07:9b
        inet 192.168.56.160 netmask 0xffffff00 broadcast 192.168.56.255
        nd6 options=29<PERFORMNUD,IFDISABLED,AUTO_LINKLOCAL>
        media: Ethernet autoselect (1000baseT <full-duplex>)
        status: active
```

Note the entry labelled `inet` and use the IP address there (and port 443), i.e. `https://192.168.56.160/briefkasten/`.

When visiting the page, enter some text into the form and add one or more attachments, then submit the form.

You should then see a success message along with a link to the feedback page for this submission.

In addition each editor email configured in `ploy.conf` should receive an email with the text of the submission and the cleansed attachments (for example, if you upload a Word document it will be sent to the editors as PDF etc.).

# Updating an existing installation

After changing your configuration, the PGP keys or the theme, the following `make` targets can be used to update a running installation:

- `make update-config` – re-applies the configuration of the application and the PGP keys
- `make upload-pgp-keys` – uploads and imports the PGP keys from `etc/pgp_pubkeys/`
- `make update-theme` – uploads the theme configured via `local_theme_path` and restarts the application
