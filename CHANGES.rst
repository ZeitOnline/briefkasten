0.3.6 - Unreleased
------------------

- MAINT: Remove obsolete deployment data for 'watchdog'

- ZO-1506: Use 'pipenv' to install 'ploy'

- ZO-1542: Let's say "hello" first

- ZO-1465: Install new certificate in crontab

- ZO-1206: Adds task to renew certificate

- ZO-1182: Collects metrics in one registry and push them once to prometheus

- ZO-1182: Adds metrics for monitoring watchdog test deliveries

- MAINT: Set up code scanning via CodeQL Analysis

- MAINT: Update python library dependencies

- MAINT: Update `cryptography` to avoid error about "loading libcrypto in an unsafe way"

- MAINT: Update Python library dependencies for application & watchdog

- MAINT: Python dependencies are handled by `tox` now

- MAINT: Build `ploy` before using it

- MAINT: Add requirements

- MAINT: No longer send emails


0.3.5 - 2021-07-27
------------------

- FIX: fix metrics meta data (again)


0.3.4 - 2021-07-27
------------------

- FIX: fix metrics meta data


0.3.3 - 2021-07-26
------------------

- ZON-6722: expose all expiry dates instead of just the most imminent one
- MAINT: fix response type for metrics


0.3.2 - 2021-07-22
------------------

- ZON-6722: expose basic prometheus metrics


0.3.1 - 2020-06-16
------------------

- Upgrade OS to 12.1-RELEASE
- Upgraded all packages to current versions
- Now using official FreeBSD packages instead of custom builds
- Upgrade appserver, worker, cleanser and watchdog to python3
- Added LetsEncrypt support


0.3.0 - 2020-03-18
------------------

- Unsupported brownbag release



0.2.17  - Unreleased
--------------------

- Upgraded OS to 11.1-RELEASE

- Upgraded all packages to current versions

- Moved package building and hosting to 'official' ``*.zeit.de`` infrastructure

- Enable optional monitoring of the jail host with zabbix

- Enable optional monitoring of the watchdog with zabbix


0.2.16  - 2018-02-12
--------------------

- Reenabled sending of uncleansed attachments via email (if no "dirty archive" has been
  configured) - this had been a regression introduced in the 0.2 branch when adding the archive
  feature

- Fixed editor template when uncleansed attachments were included (if no "dirty archive" has been
  configured) - this had been a regression introduced in the 0.2 branch when adding the archive
  feature

- Make the timeout value how long a submission token is valid configurable (instead of hard coding
  it to 10 minutes)

- Fixed various version pins and test fixtures to enable running tests in the year 2018 :)

- Upgraded OS to 10.3-RELEASE


0.2.15  - 2016-09-01
--------------------

This is the first public release of the 0.2 branch after some extensive development and in-house testing.

- major refactoring (separate web app and worker into separate code running in separate jails)
- use custom FreeBSD package repo with known-good configurations and versions which makes deployment much (much!) more stable
- use ephemeral cleanser jails
- use ephemeral storage for initial fileupload


0.1.10 - Unreleased
-------------------

 * improved watchdog deployment


0.1.9 - 2013-02-23
------------------

 * added a middleware_scripts/test_briefkasten.sh script that does local housekeeping on the server.
   The script takes the webapp directory and the pgp directory (usually ~/.gnupg/) as parameters and tries to access the public key ring. It then checks for missing keys, inaccessible keys, expired keys and keys that expire soon (or never).
   Users with keys that expire soon will receive an email, mentioning the problem. Administrators receive an email with an overview of all the problematic keys.
 * add a standalone 'watchdog' script that ensures that the whole stack is up and running as expected


0.1.8 - 2012-08-30
------------------

 * allow theming of the application via `Diazo <http://docs.diazo.org/en/latest/index.html>`_

 * remove all ZEIT ONLINE specific branding and assets from markup
   This addresses issues `#3 <https://github.com/ZeitOnline/briefkasten/issues/3>`_
   and `#10 <https://github.com/ZeitOnline/briefkasten/issues/10>`_ 
   thanks to @residuum and @Mandalka for raising the issue.

 * added BSD 3-clause license.
   This addresses `issue #8 <https://github.com/ZeitOnline/briefkasten/issues/8>`_

0.1.7 - 2012-08-08
------------------

 * generate the message to the editors via template (instead of hard-coding it in the processing shell script)

0.1.6 - 2012-08-06
------------------

 * Cosmetic tweaks

0.1.5 - 2012-08-06
------------------

 * preserve the file ending of attachments (but still replace the actual name with a random token)

0.1.4 - 2012-08-01
------------------

 * (re-) add sanitizing of office documents

0.1.3.1 - 2012-08-01
--------------------

 * fixed typo

0.1.3 - 2012-07-31
------------------

 * use a `cryptographically suitable random generator <http://docs.python.org/library/os.html#os.urandom>`_
   This addresses `issue #2 <https://github.com/ZeitOnline/briefkasten/issues/2>`_ 
   thanks to @alech (Alexander Klink) for reporting this.

 * use a `constant time comparison algorithm <http://codahale.com/a-lesson-in-timing-attacks/>`_ to avoid
   `timing attacks <https://en.wikipedia.org/wiki/Timing_attack>`_.
   This addresses `issue #4 <https://github.com/ZeitOnline/briefkasten/issues/4>`_
   thanks to @stefanw (Stefan Wehrmeyer) for reporting this.

 * generate random filenames when saving uploaded attachments.
   this is both because their names may contain compromising information but also this could otherwise
   lead to files outside the dropbox container being overwritten.
   Thanks to Alexander Klink (@alech) for pointing out this flaw.

 * Use secure rm instead of rm, if it is available.

0.1.2 - 2012-07-31
------------------

 * further cosmetic layout fixes to the upload form
 * enable submission of up to ten attachments

0.1.1 - 2012-07-31
------------------

 * apply header and footer to the submission form (since it is no longer included via an iframe).

0.1 - 2012-07-30
----------------

Initial public release
