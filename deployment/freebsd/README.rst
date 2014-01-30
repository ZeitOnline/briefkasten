Obtaining the sources
---------------------

You need to clone the entire project but then work only inside ``deployment/freebsd`` (where this README is located)::

    git clone git@github.com:ZeitOnline/briefkasten
    cd briefkasten/deployment/freebsd
    git checkout origin/freebsd-jails-with-mr.awsome


Installation using Virtualbox
-----------------------------

You need `VirtualBox <https://www.virtualbox.org>`_ with the command line tools available in your path.

- Place your public ssh key in ``roles/common/files/identity.pub``
- ``make startvm``
- wait till the login prompt
- ``make bootstrapvm``
- answer ``y`` for the questions coming up. the VM will reboot automatically after the script has run.
- after reboot run ``/bin/aws playbook vm-master.yml``
- setup the local package host: ``/bin/aws playbook poudriere.yml`` (this will take a while, it will download a ports tree and compile all packages)
- ``./bin/aws start webserver``
- ``/bin/aws playbook webserver.yml``
