# briefkasten

Anonymous submission form for the editors ("Briefkasten" = letterbox). Submitted attachments are
stripped of metadata by shell scripts, GPG-encrypted for each editor and sent by mail; the originals
are deleted. The only thing kept on the server is the status of a drop and optional editor replies.
Repo docs live in `docs/` (mkdocs, published to docs.zeit.de via the `ZeitOnline/docs` build).

Three independent uv projects, no workspace:

- `application/` — the Pyramid app, package `briefkasten` (setuptools, Python >= 3.12). Console
  scripts `worker`, `janitor`, `debug`; paste app factory `briefkasten:main`.
- `watchdog/` — `briefkasten_watchdog`, the end-to-end monitor (hatchling, src layout under
  `src/watchdog/`, Python >= 3.14). Not to be confused with the PyPI package `watchdog`, which the
  application's `worker` uses for filesystem events.
- `deployment/` — ploy/bsdploy + Ansible for FreeBSD jails (Python >= 3.12, < 3.13; `ploy`,
  `bsdploy` and `ploy-ansible` are git forks pinned in `[tool.uv.sources]`). Its `lint` dependency
  group is what CI installs for lefthook.

## How a drop moves through the system

`DropboxContainer` (`application/briefkasten/dropbox.py`) owns a drop root with `drops/<id>/`,
`submissions/`, `scratch/`, `archive_cleansed/`, `archive_dirty/`, `settings.yaml` and `metrics`.
Settings precedence: constructor kwargs > `settings.yaml` > defaults.

- The web app writes `message` and `attach/` into `drops/<id>/`, then `submit()` touches
  `submissions/<id>` and sets status `020 submitted`. It never processes anything itself.
- The `worker` command watches `submissions/`, picks up drops with `status_int == 20`, moves the
  token to `scratch/` and runs `Dropbox.process()`, which shells out to
  `<fs_bin_path>/process-attachments.sh -d <drop> -c <fs_bin_path>/briefkasten.conf`.
- The status is a three-digit code plus text in `drops/<id>/status`, written by both Python and
  the shell scripts in `application/middleware_scripts/`. Ranges drive the flow: `< 500` fine,
  `500–599` cleansing failed, `605`/`610` SMTP, `800` at least one attachment not cleansible,
  `900` success. `docs/application/workings.md` explains the intent; the individual codes there
  differ from the code, `dropbox.py` and the scripts are authoritative.
- `cleanup()` removes everything from the drop except status, editor token and replies.
- `janitor` (daily cron in the worker jail) writes `drop_root/metrics`, which the `/metrics` route
  serves as a static file, and deletes drops older than a fixed 365 days (1 day for watchdog drops).
  The `drop_ttl_days` value the deployment writes into `settings.yaml` is not read anywhere.

Routes hang off `appserver_root_url`, which must end with a slash: `{token}/submit`,
`{token}/upload`, `dropbox/{drop_id}`, `dropbox/{drop_id}/{editor_token}`. `/metrics` is absolute.
The post token is an itsdangerous `URLSafeTimedSerializer` signed with `post_secret`
(`post_token_max_age_seconds`, default 300). Editor tokens are compared constant-time via `is_equal`.

A POST whose `testing_secret` field equals the `test_submission_secret` setting is marked
`from_watchdog`: it is mailed to `watchdog_imap_recipient` instead of the editors.

## Tests

    bin/test                    # cd application && tox -> uv run py.test briefkasten/tests

`pytest` addopts enforce `--strict-config --strict-markers`, coverage and `--doctest-modules`.
Fixtures come from `briefkasten/testing.py`, registered as a pytest plugin through the `pytest11`
entry point (not a conftest); `tests/conftest.py` adds `dropbox`, `watchdog_dropbox`, `post_token`
etc. `dropbox_container` renders `tests/drop_root_template/settings.yaml` into a tmpdir, copies
`tests/gpghome/` (a real keyring, so `gpg` has to be on `PATH`) and injects `smtp=Mock()`.

The cleanser is stubbed by `tests/bin/process-attachments.sh`; `MOCKED_STATUS_CODE` selects its
outcome (`299` default, `800`, `540`, anything else fails with that code) — set it with
`monkeypatch.setenv`.

The `Dockerfile` target `backend-testing` has `ENTRYPOINT ["tox"]` and is what `testing.yaml`
builds for the shared `build-test-push` workflow. On branches, `backend-tests.yaml` only triggers
for `application/`, Docker and workflow paths; `watchdog/` and `deployment/` changes run no tests.
`watchdog/` has a `tox.ini` but no tests.

## Running locally

    cd application && uv run pserve development.ini     # http://localhost:6543/briefkasten/
    uv run worker -r var/drop_root/                      # processes submitted drops
    uv run debug -r var/drop_root/ [drop_id]             # reprocess drops in status 020

`development.ini` wires `Paste#urlmap` + the Diazo filter with `themes/fileuploader`. The local drop
root `var/drop_root/settings.yaml` uses the mocked cleanser (`fs_bin_path: briefkasten/tests/bin/`),
`~/.gnupg/` as keyring, SMTP on `localhost:8025` and `theme_package: kummerkasten_theme`, a private
package that is neither in this repo nor in `uv.lock`; `Dropbox` loads `editor_email.j2` from it,
so it has to be installed or the value changed before drops can be processed.

Stale leftovers: `application/Makefile` targets reference a `setup.py` that no longer exists,
`docs/application/develop.md` and `i18n.md` describe the Python 2.7/buildout setup, and
`docs/deployment/monitoring.md` describes the old IMAP-polling watchdog. `.travis.yml` is unused.

## Theming

Templates (`master.pt`, `dropbox_form.pt`, `feedback.pt`, `editor_reply.pt`, `editor_email.j2`)
are resolved from `theme_package` (default `briefkasten`). On top of that Diazo themes in
`application/themes/<name>/` (`rules.xml`, an HTML file, `assets/`) are applied at the WSGI
level. In deployment `use_diazo` chooses between the two: the theme directory is rsynced to
`/var/briefkasten/themes/<theme_name>` (`make update-theme`), otherwise static assets are served
from the theme package inside the jail's `.venv`.

## Watchdog

CLI `watchdog` with `submit`, `receive`, `dump`, `prune`; every option can be given as `BKWD_*`
(e.g. `BKWD_APP_URL`, `BKWD_TESTING_SECRET`, `BKWD_DBM_PATH`, `BKWD_LOG_LEVEL`). `submit` posts the
form with the testing secret and records the token in a dbm file. `receive` is an HTTP server on
port 8000 for MailJet Parse API webhooks and matches subjects against `^Drop (?P<token>...)$`.
Metrics go to a Prometheus Pushgateway (`BKWD_PROMETHEUS_PUSH_GATEWAY_URL`, job
`briefkasten_watchdog_<BKWD_ENVIRONMENT>`) with `command` as grouping key, so the short-lived
commands do not overwrite the receiver's values.

## Deployment

FreeBSD jails on one host, driven from `deployment/` with ploy (`make bootstrap`,
`configure-host`, `start-jails`, `configure-jails`, `upload-pgp-keys`, `update-config`,
`update-theme`, `update-app`). Site config lives in `deployment/etc/` (gitignored; start from
`etc.sample/`, defaults in `base.conf`). Jails: `webserver`, `appserver` (`pserve briefkasten.ini`),
`worker` (`bin/worker`), both under supervisord and sharing the `/var/briefkasten` ZFS mount, plus a
`cleanser` template jail that is snapshotted and cloned `ploy_cleanser_count` times (default 5),
dispatched by `jdispatch` and rolled back after each job. The app is installed in the jail with
`uv sync --frozen --no-install-project` from the uploaded `application/pyproject.toml` + `uv.lock`,
then `uv pip install --no-deps briefkasten`, so the jail runs the published package, not the
checkout. The Makefile exports `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` for Ansible on macOS.
Full walkthrough in `docs/deployment/index.md`.

## Conventions

- lefthook pre-commit: editorconfig-checker, `uvx ruff check`, yamllint. Ruff is configured per
  project with different line lengths: 132 (`application/`), 102 (`watchdog/`), 92 (`deployment/`).
- release-please (`release-type: python`) owns the version in `application/pyproject.toml` and
  `.release-please-manifest.json`; tags carry no `v` prefix. Conventional commits are expected.
- `bin/docs serve|html` builds the docs with the `zon-mkdocs` image; `mkdocs.yml` inherits
  `/zon/common_config.yaml` from that image.
