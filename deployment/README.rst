Installing a briefkasten instance in production
-----------------------------------------------

While the provided development.cfg makes it easy to get a local instance of the briefkasten application server up and running, setting up a secure, publicly reachable instance for real people to make submissions to is a completely different story.

Since any chain is only as strong as its weakest link, `briefkasten` comes with a set of deployment scripts that - given a simple configuration file - can install a fully functional instance, including an HTTPS capable webserver, the actual web application and a mail server to send out the encrypted submissions, all pre-configured according to what we consider best practices and ready to interact with each other.

*We currently only support FreeBSD 9*, but since the application itself is written in shell script and python and uses standard open source tools for cleaning (libre office, netpbm etc.) it should run without modification on any other sufficiently *NIX style operating system.

If you want to add another platform, take a look at `deployment/freebsd`, fork the project on github and issue a pull request :-)

For details on how to install on FreeBSD please check the ``freebsd/README.rst``.