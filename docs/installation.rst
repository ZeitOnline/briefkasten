Installation
************

Requirements
------------

The application requires Python 2.7.

Bootstrapping
-------------

Simply run::

  $ make

.. note:: you can optionally provide a custom path to your python, i.e. ``make python=/opt/local/bin/python2.7``.

Then you can start the web application like so::

  $ bin/pserve etc/briefkasten.ini

and visit `<http://localhost:6543/>`_
