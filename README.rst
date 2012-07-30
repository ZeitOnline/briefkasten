Installation
------------

Requirements
============

The application requires Python 2.7.

Bootstrapping
=============

Simply run::

  $ make

.. note:: you can optionally provide a custom path to your python, i.e. ``make python=/opt/local/bin/python2.7``.

Then you can start the web application like so::

  $ bin/pserve etc/briefkasten.ini

and visit `<http://localhost:6543/briefkasten/submit>`_

Development
-----------

The 'briefkasten' web application is developed in Python 2.7 as a `pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html/>`_ application and set up via `buildout <http://pypi.python.org/pypi/zc.buildout/>`_.

Testing
=======

Tests are run using `pytest <http://pytest.org/latest/>`_ like so::

    $ bin/test

This outputs a textbased coverage report. If that should drop below 100% you can run::

    $ bin/test-coverage

This generates a pretty report in `htmlcov/index.html` where you can browse the code and see which lines are not covered.

Internationalization
====================

All user facing text of the `briefkasen` application are translated using a ``gettext`` messsage catalog. To customize and update these messages you must:

 * install the required tools
 * update the catalog file
 * compile the catalog

Installing the required tools
*****************************

It's recommended to use virtualenv::

    virtualenv-2.7 .
    source bin/activate
    pip install lingua Babel

To find untranslated text and create entries for them, do this::

     cd src/briefkasten
     python setup.py extract_messages update_catalog

Then you can edit the message catalog in ``src/briefkasten/briefkasten/locale/XX/LCMESSAGES/briefkasten.po``

Finally (still in `src/briefkasten`)::

 python setup.py compile_catalog

After restarting the application, the new translations will be active.


Further Documentation
*********************

For more details check these links:

 * `pyramid.i18n <http://docs.pylonsproject.org/projects/pyramid/en/1.3-branch/narr/i18n.html>`_
 * `Chameleon <http://chameleon.repoze.org/docs/latest/i18n.html>`_
 * `Babel <http://babel.edgewall.org/wiki/Documentation/0.9/index.html>`_ 
