Installing a briefkasten instance in production
-----------------------------------------------

While the provided development.cfg makes it easy to get a local instance of the briefkasten application server up and running, setting up a secure, publicly reachable instance for real people to make submissions to is a completely different story.

Since any chain is only so strong as its weakest link, `briefkasten` comes with a set of deployment scripts that - given a simple configuration file - can install a fully functional instance, including an HTTPS capable webserver, the actual web application and a mail server to send out the encrypted submissions, all pre-configured according to what we consider best practices and ready to interact with each other.

We currently only support FreeBSD 9, but since the application itself is written in shell script and python and uses standard open source tools for cleaning (libre office, netpbm etc.) it should run without modification on any other sufficiently *NIX style operating system.

If you want to add another platform, take a look at `deployment/__init__.py`, fork the project on github and issue a pull request :-)

While we could simply provide pre-built installation images, this would defeat the whole idea of running a trustworthy, open source dropbox in the first place, because then you and your submitters would have to blindly trust these binaries without being able to verify their integrity.

Instead the idea is to use as little pre-built ingredients as possible and aquire them from trusted sources (i.e. from the official FreeBSD repositories). In essence we provide you with a grocery list of ingredients along with a recipe and let you do all the shopping and cooking yourself instead of serving a finished meal!


Architecture
============

The briefkasten functionality is split into three parts, each of which is installed in its own jail:

 * a webserver jail for encrypting the web traffic
 * a web application jail for receiving the submissions
 * one (or more) cleaner jails for processing the submissions
 * an email jail for sending out the encrypted submissions

The disk that hosts the jails is encrypted, so even if the server should be lost or stolen while a submission was being processed, the new owners wouldn't be able to gain access to the data.


Procedure
=========

First, we prepare the jailhost itself, then we create and configure the individual jails inside of it. However, before the scripts can run, we need to install FreeBSD itself and grant ourselves SSH access.


Installing FreeBSD on ZFS
=========================

The procedure differs slightly, depending on whether you are installing on physical hardware (recommended for production!) or on a virtual machine (recommended for testing)

Using VMWare
************

* fetch a 'Live CD' image, i.e. from here http://torrents.freebsd.org:8080/torrents/ac1303da08131c9c2fd24ad5b85a64e5fac7dfbf.torrent
* create a new machine in VMWare
    * configure the network interace in bridged mode
    * use the downloaded image as startup disk
* start the instance

Using physical hardware
***********************

To boot an actual machine you will need to download a memstick version of the Live CD, i.e. http://torrents.freebsd.org:8080/torrents/4b0a1b6096ac723a7463c64a47b3847a632560a5.torrent

Then use ``dd`` to write it to a USB stick (in Mac OS X use Disk Utility's 'Get Info' to find out which device the usb stick has, after inserting it)::

    dd if=FreeBSD-9.0-RELEASE-amd64-memstick.img of=/dev/disk3 bs=10240 conv=sync

..note: It is very importan you get the target device right, or else you might end up destroying valuable data!

You can now start the machine and it should boot from the USB stick.

Installing the OS
*****************

Virtual or real, now the machine is up and running and we can install FreeBSD. We use a helper script that allows us to install the operating system itself on ZFS, which we download

Once booted into the installer, select 'Live CD' and login as ``root`` (no password required), then::

  mkdir /tmp/bsdinstall_etc
  dhclient em0
  cd /tmp
  fetch http://anonsvn.h3q.com/s/gpt-zfsroot.sh
  sh gpt-zfsroot.sh -p da0 -s 1G -S 2G -k4 -n system -f ftp3.de.freebsd.org 
  reboot

Here we configure network access using DHCP and install a minimal FreeBSD instance. Note that you might need to adjust the ``em0`` (network interface) and ``da0`` (disk) parameters to match your hardware.

Configuring one-time SSH access
*******************************

Now we have a running operating system, but we still need to configure SSH access.

login again, then::

    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
    echo 'ifconfig_em0=DHCP' >> /etc/rc.conf
    dhclient em0
    /etc/rc.d/sshd onestart

note the IP_ADDR received, give root user a password::

    passwd

..note: Alternatively, at this point it could be a good idea to replace the DHCP configuration with a permanent, static IP address.

Now we can let the deployment scripts take over. You need a full checkout of the briefkasten repository, i.e.::

    git clone git://github.com/ZeitOnline/briefkasten.git
    cd briefkasten
    python bootstrap.py -d

But for deploying the application you only need a very minimal buildout (i.o.w. you won't need to install the whole stack and its dependencies)::

    bin/buildout -c deployment.cfg

Now the deployment scripts are ready to run. However, you still need to configure your particular installation. This is done by creating a `.ini` file. Take a look at the following example::

    [host]
    ip_addr = 10.0.10.120
    root_device = da0

    [webserver]
    ip_addr = 10.0.10.160

    [appserver]
    ip_addr = 10.0.10.161
    port = 6543
    fs_theme_path = ../themes/zeitonline


Simply call::

    bin/deploy yourconfig.ini

Look at ``deployment/freebsd/__init__.py`` to see what exactly happens...
