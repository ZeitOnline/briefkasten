Overview
--------

``briefkasten`` is a reasonably secure web application for submitting content anonymously. It allows to upload attachments which are then sanitized of a number of meta-data which could compromise the submitters identity. Next, the sanitized files are encrypted via GPG and sent via email to a pre-configured list of recipients. The original (potentially 'dirty') files are then deleted from the file system of the server. Thus, neither should admins with access to the server be able to access any submissions, nor should any of the recipients have access to the unsanitized raw material.

Upon successful upload the submitter receives a unique URL with a token that he or she can use to access any replies the recipients may post. That reply is the only data persisted on the server.

The current implementation should be ready for general use on a functional level, the only part that is (currently) hard-coded for the specific deployment at ZEIT ONLINE is the HTML markup in the templates and static assets such as logos and CSS, but these are easily modified, so in theory anybody should be able to host their own secure ``briefkasten`` with minimal setup pain.

A future release may contain more configurable options, but for now the main goal of publishing the code is transparency with re-usability coming in second.

Installation
------------

Requirements
============

The web application requires Python 2.7, the sanitizing scripts depend on a number of helper packages (such as GnuPG etc.) which are currently not yet documented.

Bootstrapping
=============

Simply run::

  $ make

**Note:** you can optionally provide a custom path to your python, i.e. ``make python=/opt/local/bin/python2.7``.

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

Roadmap
-------

While the original releases were geared towards an instance of the briefkasten application hosted by `ZEIT ONLINE <https://ssl.zeit.de/briefkasten/submit>`_ further development is planned to make the application useful 'out of the box'. In particular:

 * provide 'clean' default markup
 * provide means to customize the look of an instance without having to modify the application's markup itself
 * provide fully functional deployment scripts that create a 'best practice' installation from scratch, including web server, SSL setup, installation of all dependencies etc.
