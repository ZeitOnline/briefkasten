Installing poudriere (the build host)
-------------------------------------

.. note:: For most installations this setup is not required, as ZEIT Online already hosts the required packages for installing a complete instance.

    However, it's an important design goal of the briefkasten stack that the entire stack is open source and can be replicated and verified by third parties, which is why the setup of the auxiliary infrastructure is part of this project, as well.


The Briefkasten deployment relies on a custom package host that provides the pre-configured, pre-built binary packages to install into the respective jails (i.e. built with libressl, custom build options for libreoffice etc.)

This section describes how to setup such a build host and how to serve the assets that it creates.

The build host is configured using the `poudriere` role (poudriere is the name of the software that builds the packages) and is expected to be run against a FreeBSD host system (i.e. not inside a jail) with the same or larger major version of the briefkasten system. 

The build host requires a private key with which it signs all builds (and whose public key is installed on the briefkasten host).
This key is (obviously) not part of the open source repo and is instead expected to reside in a toplevel folder named `files` next to the checkout of the `briefkasten` repo.


Hosting the packages
--------------------

Hosting the packages is typically done on another host which only needs a webserver and some space.

The host uses a self-signed key for serving via HTTPS. This is done for two reasons:
a) we don't have to install the 'official' certs on the briefkasten (which means that it won't trust any other sites than our own host)
b) for an attacker to spoof our packages he must also spoof our private key instead of just using any valid certificate out there. (admittedly, this is a fairly esoteric edgecase...)