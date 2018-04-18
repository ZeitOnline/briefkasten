Installation
------------

Requirements
============

The web application requires only Python 2.7, the sanitizing scripts depend on a number of helper packages (such as GnuPG, LibreOffice etc.).

This means that it's a viable option for developing the web application and/or developing a theme for it to bypass the deployment of the whole stack (which depends on FreeBSD as the OS) and instead just install the 'naked' web application locally on any platform that supports Python 2.7.


Bootstrapping
=============

Change into the application directory and run::

  $ cd application
  $ make

**Note:** you can optionally provide a custom path to your python, i.e. ``make python=/opt/local/bin/python2.7``.

Then you can start the web application like so::

  $ bin/pserve briefkasten.ini

and visit `<http://localhost:6543/submit>`_


Customization
-------------

The briefkasten application deliberately only serves a very minimalistic markup by default. While you could go ahead and fork the project and modifiy the templates directly, that is not encouraged. Instead we provide a generic 'theming' approach using `Diazo <http://docs.diazo.org/en/latest/index.html>`_, where you simply add static HTML and CSS files which are then applied at runtime to the application's markup.

This means you neither have to learn how the application works in detail nor do you risk accidentally breaking its functionality.


Changing the default look
=========================

To change the default look you need to do four things:

 * create a theme directory
 * add the path to the buildout configuration file
 * re-run buildout
 * restart the application

A theme directory must conform to the following structure::

    rules.xml
    theme.html
    assets/

``rules.xml`` must be a valid diazo rule, which needs to point to (at least) one html template (i.e. ``theme.html``). Any files located inside the ``assets/`` directory can be referenced from the theme, so you can add any images, CSS, JS and whatnot there. It's best to reference those assets with relative paths, that way you can develop the theme simply by opening the theme HTML file in a browser.

For further information on how to create additional rules see the `official Diazo documentation <http://docs.diazo.org/en/latest/basic.html>`_.

To use the theme, point the buildout to it. The easiest way is to replace the ``buildout.cfg`` symlink that the Makefile created with an actual file containing the following stub::

    [buildout]
    extends = development.cfg

    [config]
    fs_theme_path = XXXX

Where ``XXXX`` is the absolute path to the theme you created. Note that you can use the following syntax to refer to a location relative to the project file path::

    [config]
    fs_theme_path = ${buildout:directory}/themes/mycustomtheme

Once you've done this, you need to re-run buildout like so::

    bin/buildout -No

(The ``-No`` flags force buildout to run in offline mode, thus speeding the process up significantly, since we're only regenerating the configuration)

You then need to restart the application, i.e. by hitting ``CTRL-c`` in the foreground process and re-running ``bin/pserve briefkasten.ini``.

Once you've performed these steps you can keep the server running while you're developing the theme, because in debug mode changes to the theme and the rules are picked up instantly without requiring a restart.

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
