Development
-----------

The 'briefkasten' web application is developed in Python 2.7 as a `pyramid <http://docs.pylonsproject.org/en/latest/docs/pyramid.html/>`_ application, set up via `buildout <http://pypi.python.org/pypi/zc.buildout/>`_ and documented with
`sphinx <http://sphinx.pocoo.org/>`_.

See :doc:`installation` for Installation instructions.

Testing
-------

Tests are run using `pytest <http://pytest.org/latest/>`_ like so::

    $ bin/test

This outputs a textbased coverage report. If that should drop below 100% you can run::

    $ bin/test-coverage

This generates a pretty report in `htmlcov/index.html` where you can browse the code and see which lines are not covered.
