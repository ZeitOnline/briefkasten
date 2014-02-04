Obtaining the sources
---------------------

You need to clone the entire project but then work only inside ``deployment/freebsd`` (where this README is located)::

    git clone git@github.com:ZeitOnline/briefkasten
    git checkout -t origin/freebsd-jails-with-mr.awsome
    cd briefkasten/deployment/freebsd


Installation using Virtualbox
-----------------------------

You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- Place your public ssh key in ``roles/common/files/identity.pub``
- ``make startvm``
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

Make sure the output matches the one in the downloaded text. Return into the deployment directory ``cd ..``.


Creating a bootable USB medium (Mac OSX)
========================================

- Run ``diskutil list`` to see which drives are currently in your system.
- insert your medium
- re-run ``diskutil list`` and notice which number it has been assigned (N)
- run ``diskutil unmountDisk /dev/diskN``
- run ```sudo dd if=mfsbsd-se-9.2-RELEASE-amd64.img of=/dev/diskN bs=1m``
- run ``diskutil unmountDisk /dev/diskN``

Boot the machine. Log in as root using the pre-configured password ``mfsroot``. Note the name of the ethernet interface and the IP address it has been given by running ``ifconfig``.

Run ``gpart list`` and note the device name of the hard drive. Enter these values into your ``etc/aws.conf``.


Bootstrapping the host
----------------------

- run ``make bootstraphost``
- answer ``y`` for the questions coming up. the host will reboot automatically after the script has run.
- at the end of the script run, the script will output the fingerprint it has generated for the SSH daemon on the host. You *must* enter that in in the ``[ez-master:vm-master]`` section of your ``aws.conf`` as ``fingerprint =``.
- in the meantime the host has probably finished rebooting. Now run ``./bin/aws playbook provisioning/vm-master.yml``
- setup the local package host: ``./bin/aws playbook setup/poudriere.yml`` (this will take a while, it will download a ports tree and compile all packages)
- ``./bin/aws start webserver``
- either put a valid cert and key into ``setup/roles/webserver/files/briefkasten.(crt|key)`` or run ``make cert`` to create a self-signed one
- now you can configure the webserver jail: ``/bin/aws playbook webserver.yml``
