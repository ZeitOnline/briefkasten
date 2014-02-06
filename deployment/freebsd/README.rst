Obtaining the sources
---------------------

You need to clone the entire project but then work only inside ``deployment/freebsd`` (where this README is located)::

    git clone git@github.com:ZeitOnline/briefkasten
    cd briefkasten
    git checkout -t origin/freebsd-jails-with-mr.awsome
    cd deployment/freebsd

Installing the requirements
---------------------------

The system needs **Python 2.7** with ``virtualenv`` and ``make``.


Configuring your setup
----------------------

Before we can continue, we need to configure your setup. The deployment needs four assets, most of which need to reside inside ``etc``:

- ``etc/aws.conf`` - the **main configuration file** for the jail host and jails. See ``aws.conf.sample`` for details.
- ``provisioning/vm-master/identity.pub`` – your **SSL public key**. This will be uploaded to the host.
- One or more **PGP keys** located inside ``etc/pgp_pubkeys/`` – these will be used to encrypt the submissions
- ``etc/briefkasten.crt`` and ``etc/briefkasten.key`` – the SSL key and certificate of the webserver that will server the app. This is optional during development and testing, if you provide none a self-signed setup will be generated for your convenience

Installation using Virtualbox
-----------------------------

You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- ``make start-vm``
- wait till the login prompt
- Continue with **Bootstrapping the host**


Installation using VMWare
-------------------------

First get the image::

	make mfsbsd_download

This downloads the ISO image into the ``downloads`` folder. In VMWare create a virtual machine and boot it from that image. At the login prompt log in with username/password ``root/mfsroot``. Use ``ifconfig`` to get the assigned IP address and enter it into ``aws.conf``.

- Continue with **Bootstrapping the host**


Installation on physical hardware
---------------------------------

Download the MFSBSD ISO image and checksum::

	cd downloads
	wget http://mfsbsd.vx.sk/files/images/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.img
	wget http://mfsbsd.vx.sk/files/images/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.img.sums.txt

Verify the integrity of the downloaded image::

	shasum mfsbsd-se-9.2-RELEASE-amd64.img

Make sure the output matches the one in the downloaded text.


Creating a bootable USB medium (Mac OSX)
========================================

- Run ``diskutil list`` to see which drives are currently in your system.
- insert your medium
- re-run ``diskutil list`` and notice which number it has been assigned (N)
- run ``diskutil unmountDisk /dev/diskN``
- run ```sudo dd if=mfsbsd-se-9.2-RELEASE-amd64.img of=/dev/diskN bs=1m``
- run ``diskutil unmountDisk /dev/diskN``

Boot the machine. Log in as root using the pre-configured password ``mfsroot``. Note the name of the ethernet interface and the IP address it has been given by running ``ifconfig``.

Run ``gpart list`` and note the device name of the hard drive. Enter these values into your ``etc/aws.conf``. Return into the deployment directory ``cd ..``.


Bootstrapping the host
----------------------

The functionality of the briefkasten has been split into three jails: a **webserver** jail that only contains the frontend, an **appserver** jail that contains the web application that handles the submissions and a separate **cleanser** jail that only deals with sanitizing and anonymizing any submitted attachments.

Once we have a running host we can prepare for running these jails like so:

- run ``make bootstrap-host``
- answer ``y`` for the questions coming up. the host will reboot automatically after the script has run.
- at the end of the script run, the script will output the fingerprint it has generated for the SSH daemon on the host. You *must* enter that in in the ``[ez-master:vm-master]`` section of your ``aws.conf`` as ``fingerprint =``.
- in the meantime the host has probably finished rebooting. Now run ``make configure-host``
- setup the local package host: ``make setup-poudriere``
- if this is the first time you've setup a system you will need to build the required packages - this will take quiet a while as it will download a ports tree and compile all packages. Run ``make build-packages``.

Now we have all requirements in place to install the jails.


Installing the jails
--------------------

- First start and create the (empty) jails ``make start-jails``.
- Configure the webserver jail: ``make configure-webserver``
- Configure the appserver jail: ``make configure-appserver``
- Configure the cleanser jail: ``make configure-cleanser``
