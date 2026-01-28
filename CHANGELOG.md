# Changelog

## [0.5.0](https://github.com/ZeitOnline/briefkasten/compare/0.4.0...0.5.0) (2026-01-28)


### Features

* **deployment:** switch to `uv` for managing dependencies ([#458](https://github.com/ZeitOnline/briefkasten/issues/458)) ([2bed149](https://github.com/ZeitOnline/briefkasten/commit/2bed149f73a384c70afbe1b071d38fe877b384b9))
* use 'lefthook' to run code checks via git hooks ([#468](https://github.com/ZeitOnline/briefkasten/issues/468)) ([13a4922](https://github.com/ZeitOnline/briefkasten/commit/13a4922ebea2b52a5847138cd79896787782180b))

## [0.4.0](https://github.com/ZeitOnline/briefkasten/compare/0.3.14...0.4.0) (2025-08-29)


### Features

* **mail:** allow to store the smtp password encrypted ([69c408f](https://github.com/ZeitOnline/briefkasten/commit/69c408f1a62fec85da12e7adeea5d137262cbbc5))


### Bug Fixes

* update the company name ([cfda8d2](https://github.com/ZeitOnline/briefkasten/commit/cfda8d28602891de55de40a1f372096d23a80484))

## [0.3.14](https://github.com/ZeitOnline/briefkasten/compare/0.3.13...0.3.14) (2025-05-14)


### Bug Fixes

* **smtp:** allow to actually use TLS (servers) ([#402](https://github.com/ZeitOnline/briefkasten/issues/402)) ([950418c](https://github.com/ZeitOnline/briefkasten/commit/950418cde30461fd084ea655aec499e3d7d6a600))

## 0.3.13 - 2025-01-09

- docs: convert change log to markdown
- chore(deps): sync dependencies between `Pipfile` and `requirements.txt`
- fix: adjust path to 'cleaner' home directory to make ssh work
- fix: change pyramid's home directory in playbooks
- chore(deps): upgrade application & deployment dependencies
- chore: upgrade to FreeBSD 14.2
- chore(deps): switch to a more recent Python (3.11)
- docs: migrate to mkdocs
- docs: convert documentation to Markdown
- docs: add section about how to run ploy with 'pipenv'
- fix(ci): use `include_tasks` instead of the deprecated `ansible.builtin.include`
- ZO-4618: set `Strict-Transport-Security` header (HSTS)
- ZO-942: configure 'setuptools' and 'pytest' via `pyproject.toml`
- chore(watchdog): remove explicit package dependencies
- chore(watchdog): clean up package dependencies
- ZO-3365: split up and refactor test submission and receiver
- fix: fix expressions used for conditionals
- fix: use fix for connection timing handling in 'ploy'
- fix: use `extra_zfs_properties` parameter with the 'zfs' module
- chore: remove explicit package dependencies
- chore: use 'renovate' instead of 'dependabot'
- chore: drop 'setuptools-git-version'
- chore: use 'pipenv' to upgrade package dependencies
- fix: expand user directory in path to GPG keys
- style: fix various 'flake8' warnings
- chore: add 'pre-commit' configuration
- chore: log submission requests more verbosely

## 0.3.12 - 2023-06-02

- MAINT: Log submission requests more verbose

## 0.3.11 - 2023-01-20

- FIX: Removes whitespaces in textarea

## 0.3.10 - 2023-01-20

- FIX: Adds missing divs

## 0.3.9 - 2023-01-19

- ZO-2217: Changes template text

## 0.3.8 - 2023-01-18

- MAINT: Make some template form text changes
- MAINT: Fix certificate cronjob
- MAINT: Upgrade OS to 12.3-RELEASE
- MAINT: Switch to "webroot mode" as the default ACME mode
- MAINT: Remove obsolete 'poudriere' setup
- MAINT: Add missing dependencies
- MAINT: Update python library dependencies

## 0.3.7 - 2022-07-08

- MAINT: Remove obsolete deployment data for 'watchdog'
- MAINT: Update python library dependencies
- ZO-1506: Use 'pipenv' to install 'ploy'
- ZO-1542: Let's say "hello" first

## 0.3.6 - 2022-06-21

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

## 0.3.5 - 2021-07-27

- FIX: fix metrics meta data (again)

## 0.3.4 - 2021-07-27

- FIX: fix metrics meta data

## 0.3.3 - 2021-07-26

- ZON-6722: expose all expiry dates instead of just the most imminent one
- MAINT: fix response type for metrics

## 0.3.2 - 2021-07-22

- ZON-6722: expose basic prometheus metrics

## 0.3.1 - 2020-06-16

- Upgrade OS to 12.1-RELEASE
- Upgraded all packages to current versions
- Now using official FreeBSD packages instead of custom builds
- Upgrade appserver, worker, cleanser and watchdog to python3
- Added LetsEncrypt support

## 0.3.0 - 2020-03-18

- Unsupported brownbag release

## 0.2.17  - Unreleased

- Upgraded OS to 11.1-RELEASE
- Upgraded all packages to current versions
- Moved package building and hosting to 'official' `*.zeit.de` infrastructure
- Enable optional monitoring of the jail host with zabbix
- Enable optional monitoring of the watchdog with zabbix

## 0.2.16  - 2018-02-12

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

## 0.2.15  - 2016-09-01

This is the first public release of the 0.2 branch after some extensive development and in-house testing.

- Major refactoring (separate web app and worker into separate code running in separate jails)
- Use custom FreeBSD package repo with known-good configurations and versions which makes deployment much (much!) more stable
- Use ephemeral cleanser jails
- Use ephemeral storage for initial fileupload

## 0.1.10 - Unreleased

- Improved watchdog deployment

## 0.1.9 - 2013-02-23

- Added a middleware_scripts/test_briefkasten.sh script that does local housekeeping on the server.
  The script takes the webapp directory and the pgp directory (usually ~/.gnupg/) as parameters and tries to access the public key ring. It then checks for missing keys, inaccessible keys, expired keys and keys that expire soon (or never).
  Users with keys that expire soon will receive an email, mentioning the problem. Administrators receive an email with an overview of all the problematic keys.
- Add a standalone 'watchdog' script that ensures that the whole stack is up and running as expected

## 0.1.8 - 2012-08-30

- Allow theming of the application via [Diazo](http://docs.diazo.org/en/latest/index.html)
- Remove all ZEIT ONLINE specific branding and assets from markup
  This addresses issues [#3](https://github.com/ZeitOnline/briefkasten/issues/3)
  and [#10](https://github.com/ZeitOnline/briefkasten/issues/10)
  thanks to @residuum and @Mandalka for raising the issue.
- Added BSD 3-clause license.
  This addresses [issue #8](https://github.com/ZeitOnline/briefkasten/issues/8)

## 0.1.7 - 2012-08-08

- Generate the message to the editors via template (instead of hard-coding it in the processing shell script)

## 0.1.6 - 2012-08-06

- Cosmetic tweaks

## 0.1.5 - 2012-08-06

- Preserve the file ending of attachments (but still replace the actual name with a random token)

## 0.1.4 - 2012-08-01

- (Re-) add sanitizing of office documents

## 0.1.3.1 - 2012-08-01

- Fixed typo

## 0.1.3 - 2012-07-31

- Use a [cryptographically suitable random generator](http://docs.python.org/library/os.html#os.urandom)
  This addresses [issue #2](https://github.com/ZeitOnline/briefkasten/issues/2)
  thanks to @alech (Alexander Klink) for reporting this.
- Use a [constant time comparison algorithm](http://codahale.com/a-lesson-in-timing-attacks/) to avoid
  [timing attacks](https://en.wikipedia.org/wiki/Timing_attack).
  This addresses [issue #4](https://github.com/ZeitOnline/briefkasten/issues/4)
  thanks to @stefanw (Stefan Wehrmeyer) for reporting this.
- Generate random filenames when saving uploaded attachments.
  this is both because their names may contain compromising information but also this could otherwise
  lead to files outside the dropbox container being overwritten.
  Thanks to Alexander Klink (@alech) for pointing out this flaw.
- use secure rm instead of rm, if it is available.

## 0.1.2 - 2012-07-31

- Further cosmetic layout fixes to the upload form
- Enable submission of up to ten attachments

## 0.1.1 - 2012-07-31

- Apply header and footer to the submission form (since it is no longer included via an iframe).

## 0.1 - 2012-07-30

- Initial public release
