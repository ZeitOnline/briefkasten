Overview
--------

``briefkasten`` is a reasonably secure web application for submitting content anonymously. It allows to upload attachments which are then sanitized of a number of meta-data which could compromise the submitters identity. Next, the sanitized files are encrypted via GPG and sent via email to a pre-configured list of recipients. The original (potentially 'dirty') files are then deleted from the file system of the server. Thus, neither should admins with access to the server be able to access any submissions, nor should any of the recipients have access to the unsanitized raw material.

Upon successful upload the submitter receives a unique URL with a token that he or she can use to access any replies the recipients may post. That reply is the only data persisted on the server.

The current implementation should be ready for general use on a functional level, so in theory anybody should be able to host their own secure ``briefkasten`` with minimal setup pain.

A future release may contain more configurable options, but for now the main goal of publishing the code is transparency with re-usability coming in second.

Installation
------------

Requirements
============

The web application requires Python 2.7, the sanitizing scripts depend on a number of helper packages (such as GnuPG etc.) which are currently not yet documented.

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

Monitoring
==========

Since the whole system is configured by design not to log anything in order to protect the identity of submitters in case of a break-in, it is pretty much impossible to perform any post-mortem anyalysis when something has gone wrong. At the same time it is vital that you can be sure that the system is up and running at all times. Even if the web application is running and submitters can post data (and even receive a token as confirmation) any other part of the chain (sanitizing, encrypting and sending of the submitted material) could be broken without anybody noticing it. To this end, we've included a dedicated **watchdog** application which performs regular **end to end** tests of a ``briefkasten`` instance.

Ideally, the watchdog is installed on another machine, preferably on another network (afterall, that's where your users will be coming from, too).

To install it, use a checkout of this project but use the ``watchdog.cfg`` configuration for running buildout, like so::

    $ bootstrap -c watchdog.cfg
    $ bin/buildout -c watchdog.cfg

    ..TODO: provide a ``make watchdog`` target.

This will install an executable in ``bin/watchdog`` which is designed to be called without parameters, i.e. from a ``crontab`` entry.

It expects its configuration in ``etc/watchdog.ini`` with the following values::

    app_url = # full URL to the submit form, i.e. ``https://ssl.zeit.de/briefkasten/submit``
    test_token = # a unique string that will trigger the test submission when the watchdog submits a POST
    max_process_secs = # time in seconds which it allows a submission to take to complete before it deems it failed.
    imap_recipient = # email address to which the test submission should be sent to
    imap_host =
    imap_user =
    imap_passwd =
    notify_email = one or more (one per line) email recipients that should receive notification if something went wrong.
    # smtp settings for pyramid_mailer, see
    # http://docs.pylonsproject.org/projects/pyramid_mailer/en/latest/
    smtp_host = localhost
    smtp_port = 25
    smtp_username = blubber
    smtp_password = fooberific
    smtp_tls = true

When run, the script will:

 * log into the IMAP account and retrieve any new emails that look like a ``briefkasten`` submission, noting their token in a timestamped list of actually received notifications.
 * it then compares this list with the ones it expects a submission for. any tokens found are removed.
 * any tokens remaining with a time stamp older than the maximum allowed processing time trigger a notification email.
 * next, it performs a test submission at the given url. It sends the preconfigured token using a ``X-Briefkasten-Testing-Token`` header in the request.
 * it then parses the response and stores the token received in the list for which it expects a submission.
 * If anything went wrong during that process it sends out the notification(s) and terminates.

Note, that unlike the application itself, the watchdog does keep detailed logs of all the steps described above, allowing some minimal post-mortem analysis without compromising actual 'real world' submissions.

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

     python setup.py extract_messages update_catalog

Then you can edit the message catalog in ``briefkasten/locale/XX/LCMESSAGES/briefkasten.po``

Finally::

 python setup.py compile_catalog

After restarting the application, the new translations will be active.

For more details check these links:

 * `pyramid.i18n <http://docs.pylonsproject.org/projects/pyramid/en/1.3-branch/narr/i18n.html>`_
 * `Chameleon <http://chameleon.repoze.org/docs/latest/i18n.html>`_
 * `Babel <http://babel.edgewall.org/wiki/Documentation/0.9/index.html>`_ 


The life cycle of a submission
******************************

Users entrusting us with sensitive data is the key concern of the software and when and getting it straight where this data is stored for how long in what form is crucial.

The stages are numbered with a three digit integer code, allowing to group and sort them.

Status codes beginning with `0` mean that the submission is still being handled by the web application (and implies that it is still unencrypted)

The life of a submission begins with the POST of the client browser succeeding.
Any attachments are first stored in memory before writing them to disk into a dedicated dropbox directory.
At this point the submission has the status `010 received` and is readable in plaintext by any attacker who gains access to the application jail.

Next, the web application hands off the submission to an external processing script, which immediately either errors out or acknowledges the receipt of the drop directory.

The error case at this stage means that the cleansing setup is seriously broken and the web application will take it upon itself to delete the attachments immediately to avoid exposing them in plaintext unduly.
(TODO: a cronjob on the jailhost should additionally monitor for dropboxes in the 'submitted' or 'submitted failed' state for longer than a given threshold)

If the submission was successful (the process script returns `0` as exit code) the dropbox is considered to be `020 submitted`.

Once submitted, the cleanser performs basic sanity checking. If that fails for whatever reason it will set the status to `500 cleanser init failure`. Since it's basically being able to accept the attachments it will delete the attachment itself (TODO: confirm with @erdgeist)

If the process script determines that the cleansing setup is intact (whether locally or via one or more cleanser jails) it will set the status to `100 processing`.
The submission still resides in plaintext inside the application jail.

The process will now initiate the cleansing, either locally or by submitting it to a cleanser jail. Either way, once the submission is sucessful, the status will change to `200 quarantined`, and the submission is (finally) no longer readable inside the application jail.

If submission has failed the status will be set to `501 cleanser submission failure` and the attachments will be deleted.

Now we are left with three possible outcomes: success, failure during cleansing or timeout:

- `510 cleanser processing failure`
- `520 cleanser timeout failure`
- `900 success`

In all cases except `900` the attachments will have been deleted from the fileystem of the briefkasten host.


Further Documentation
*********************


TODO
====

general bugs
------------

X fix claim mechanism

X investigate 'heisenbug'

- update docs re: `source bin/activate`

x ensure appserver is running after config changes

X ensure testing secret is present in themed forms

x use private devpi with git-setuptools-version



feature: refactor process workflow
----------------------------------

- break into wrapping `process` call which will catch any exceptions and set the status accordingly
  and will also be responsible for calling cleanup

- `Dropbox.process` is

  x the only entry point into and encapsulates the entire cleansing process

  x a long-running, synchronous call that always succeeds (to the caller)

  x but catches underlying failures and updates the status of the dropbox accordingly

  x always calls cleanup

  x separate 'private' tasks:

  x if we have attachments:

    x create uncleansed, encrypted fallback copy of attachments
      - failures:
        - no valid keys

    x clean attachments (this also encrypts them)
      - failures:
        x no cleansers configured
        x no cleansers available
        - time-out

    x archive clean attachments if cleaning was successful and size is over limit

    - archive uncleaned attachments if cleaning failed
      (re-uses the initially created encrypted backup before that is wiped during cleanup)

    x notify editors via email

      x (include cleaned attachments if cleaning was sucessful and size below limit)
      x otherwise include link to share


feature: large attachments support
----------------------------------

 x calculate total size of attachments

 x add configurable threshold value (support MB/GB via humanfriendly)

 x configure cleansed/uncleansed file system paths

 x configure formatstrings to render them as shares


feature: asynchronous workers
-----------------------------

x separate worker process (either using celery, or a custom worker)

x runs in separate jail with mapped dropbox container file system

x reads identical confguration on init

x watches for appearance of new dropboxes and reacts to according to their status

x keep dropbox specific settings in settings.json file inside container directory, only keep pyramid specific settings in .ini file (including path to dropbox container)

TODOS:

 x create `worker` entry point

 x create supervisord config for worker

 x create configuration reader (hardcode python dict for now)

 x factor rendering of email text out of pyramid view into separate dropbox subtask


feature: re-activate watchdog feature
-------------------------------------

 x set recipients to configured watchdog address instead of editors

 - integrate watchdog setup into makefile and base.conf

 - configure watchdog without buildout and from ploy.conf values


feature: local janitor (in python)
----------------------------------

 - create cronjob (in worker jail)

 - write tests for erdgeist's python code :)
