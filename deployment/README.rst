Overview
--------

While we could simply provide pre-built installation images, this would defeat the whole idea of running a trustworthy, open source dropbox in the first place, because then you and your submitters would have to blindly trust these binaries without being able to verify their integrity.

Instead the idea is to use as little pre-built ingredients as possible and aquire them from trusted sources (i.e. from the official FreeBSD repositories). In essence we provide you with a grocery list of ingredients along with a recipe and let you do all the shopping and cooking yourself instead of serving a pre-cooked meal!

An instance of the briefkasten is deployed by running scripts on a *control host* (i.e. your local machine) which then configure and install it on a *target host* (i.e. virtual machine for development and testing, on dedicated hardware for production).

During this process the *target host* will boot from a FreeBSD installer medium (ISO image or USB stick), then (remotely) receive instructions to install itself on the *target host* with a minimal configuration, boot into that system and then finalize the installation.


Obtaining the sources
---------------------

You need to clone the entire project onto the *control host* but will then work only inside ``deployment`` (where this README is located)::

    git clone https://github.com/tomster/briefkasten.git
    cd briefkasten/deployment


Installing the requirements on the control host
-----------------------------------------------

The *control host* needs **Python 2.7** with ``virtualenv`` and ``make``.

On most Linux distributions you should get all of the above by installing ``python-virtualenv`` (i.e. ``aptitude install python-virtualenv``).

Under Mac OS X using `homebrew <http://brew.sh>`_ is the recommended way (``brew install python`` should do the trick.) (The Python installation that's part of Mac OS X ships without ``virtualenv`` and is out-dated. It's best to ignore it entirely.

Under FreeBSD install ``devel/py-virtualenv``.


Configuring your setup
----------------------

Before we can continue, we need to configure your setup on the *control host*. The deployment scripts require four assets, most of which need to reside inside ``etc``.

In practice it is advisable to keep the entire ``etc`` under separate version control – it contains everything that distinguishes your particular setup from a generic one. A good start is to copy ``etc.sample`` to ``etc`` and perform a ``git init`` inside it. YMMV.


ploy.conf – the main configuration file
=======================================

Create your own configuration directory inside::

  $ mkdir etc

Create a copy from the provided example::

  $ cp etc.sample/ploy.conf etc/

If you want to use VirtualBox to try out the installation on a local virtual machine, you can copy ``etc.sample/vbox.conf`` instead, which contains a ready-to-use setup. 

You will (at least) need to provide values in the ``[ez-master:briefkasten]`` section for the following keys:

  - host
  - port

Note that you cannot specify the SSH fingerprint at this time yet, you need to wait until after ``bootstrap-host`` has run (see below)

And in the ``[macro:ez-base]`` section for these:

	- ansible-fqdn
	- approot_url
	- editors
	- admins
	- mail_sender
	- local_theme_path
	- theme_name

Look inside the file for details, it should be self explanatory.


SSH public key
==============

This key (usually ``~/.ssh/idenity.pub``) will be installed on the *target host* during bootstrapping and will enable access to it.

You need to place it inside ``etc/authorized_keys``.


Editorial PGP keys
==================

For each email address configured as recipient of the submissions in ``ploy.conf`` you must provide a matching public PGP key which will be used to encrypt the submissions.

These need to reside inside ``etc/pgp_pubkeys/`` and are expected to end in ``*.gpg``. You can use one key per editor or any public keyring format that is understood by ``gnupg``.


SSL certificate for the webserver
=================================

The webserver will be configured to communicate exclusively via HTTPS – to this end you will need to provide a suitable certificate/key pair. It is expected in ``etc/briefkasten.crt`` and ``etc/briefkasten.key`` respectively, ``etc.sample`` contains a self-signed pair for development and testing purposes.


Booting the target host into FreeBSD
------------------------------------

Next we will need to boot the *target host* into the FreeBSD installer. Since an official vanilla installer from freebsd.org would require quite a bit more manual configuration we instead use a slightly modified version of this called `MFSBSD <http://mfsbsd.vx.sk>`_ – it basically attempts to configure the network via DHCP and has SSH enabled for ``root`` with a defined password of ``mfsroot``.


Installation using Virtualbox
=============================

This is the recommended way for testing and developing, as it allows for 100% automation. You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- ``bin/ploy start briefkasten-vbox`` – this will download the ISO image, create a virtual machine and boot it from the image
- wait till the login prompt - we're now booted into the MFSBSD installer
- Continue with **Bootstrapping the host**


Installation using VMWare
=========================

First download the image::

    mkdir downloads
    bin/ploy-download  http://mfsbsd.vx.sk/files/images/10/amd64/mfsbsd-se-10.2-RELEASE-amd64.img 72664ced483bc69ae27bb1467bca0e678e1d6440 downloads/

This downloads the ISO image into the ``downloads`` folder. In VMWare create a virtual machine and boot it from that image. At the login prompt log in with username/password ``root/mfsroot``. Use ``ifconfig`` to get the assigned IP address (or assign one manually) and enter it into ``ploy.conf``.

- Continue with **Bootstrapping the host**


Installation on physical hardware
=================================

This is the recommended setup for production. The machine doesn't need to be particularly powerful, but it will require at least 2Gb RAM and 10Gb disk space to compile the packages.

Download the MFSBSD ISO image and checksum::

	cd downloads
	wget http://mfsbsd.vx.sk/files/images/10/amd64/mfsbsd-se-10.2-RELEASE-amd64.img
	wget http://mfsbsd.vx.sk/files/images/10/amd64/mfsbsd-se-10.2-RELEASE-amd64.img.sums.txt

Verify the integrity of the downloaded image::

	shasum mfsbsd-se-10.2-RELEASE-amd64.img

Make sure the output matches the one in the downloaded text. Next you will need to create a bootable medium from that image.


Creating a bootable USB medium (Mac OSX)
****************************************

For the time being we only provide instructions for Mac OS X, sorry! If you run Linux you probably already know how to do this, anyway :-)

- Run ``diskutil list`` to see which drives are currently in your system.
- insert your medium
- re-run ``diskutil list`` and notice which number it has been assigned (N)
- run ``diskutil unmountDisk /dev/diskN``
- run ```sudo dd if=mfsbsd-se-10.2-RELEASE-amd64.img of=/dev/diskN bs=1m``
- run ``diskutil unmountDisk /dev/diskN``

Insert the USB stick into the *target host* and boot from it. Log in as ``root`` using the pre-configured password ``mfsroot``. Either note the name of the ethernet interface and the IP address it has been given by running ``ifconfig`` or set them to the desired values in ``/etc/rc.conf`` if you do not have a DHCP environment.

Run ``gpart list`` and note the device name of the hard drive(s). Enter this values into your ``etc/ploy.conf``.

Return into the deployment directory ``cd ..``.



Bootstrapping the target host
-----------------------------

Either way you now should have *target host* booted into MFSBSD with a known IP address which has been entered into ``etc/ploy.conf`` and we can continue.

The functionality of the briefkasten has been split into three jails: a **webserver** jail which only contains the frontend, an **appserver** jail which contains the web application that handles the submissions and a separate **cleanser** jail that only deals with sanitizing and anonymizing any submitted attachments.

Since we have a running host we can prepare for these jails like so:

- run ``make bootstrap`` on the *control host*
- answer ``y`` for the questions coming up. the host will reboot automatically after the script has run.
- at the end of the script run, the script will output the fingerprint it has generated for the SSH daemon on the host. You *must* enter that in in the ``[ez-master:briefkasten]`` section of your ``ploy.conf`` as ``fingerprint =``.
- in the meantime the *target host* has probably finished rebooting. Now run ``make configure-host``

Anyway, now we have all requirements in place to install the jails.


Installing the jails
--------------------

First start and create the (empty) jails ``make start-jails``, then configure them: ``make configure-jails``.

Finally, you need to upload and install the PGG keys of the editors and admins: ``make upload-pgp-keys``.

You now should be able to visit the configured https URL in your browser. In the case of virtualbox ``https://localhost:47023/briefkasten/submit``.


Testing the installation
------------------------

Once all steps have been completed successfully you should be able to visit the briefkasten in a webbrowser.

in the case of testing via virtualbox the url would be `https://localhost:47023/briefkasten/submit <https://localhost:47023/briefkasten/submit>`_.

When visiting the page, enter some text into the form and add one or more attachments, then submit the form.

You should then see a success message along with a link to the feedback page for this submission.

In addition each editor email configured in ``ploy.conf`` should receive an email with the text of the submission and the cleansed attachments. (for example, if you upload a word document it will be sent to the editors as PDF etc.).


Installing the watchdog
-----------------------

The watchdog should be installed on a third host (IOW neither on the target host, nor the control host).

In your ``ploy.conf`` you need to define its IP address and port and assign it the ``watchdog`` role.

