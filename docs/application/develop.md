# Installation

## Requirements

The web application requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/) for managing its dependencies. The test suite additionally needs [GnuPG](https://gnupg.org) to be installed. The sanitizing scripts depend on a number of further helper packages (such as LibreOffice etc.), which are only needed for actually processing submissions.

This means that for developing the web application and/or a theme for it you can bypass the deployment of the whole stack (which depends on FreeBSD as the OS) and instead just install the 'naked' web application locally on any platform that supports Python.

## Bootstrapping

Change into the application directory and install the dependencies:

```
$ cd application
$ uv sync --frozen
```

This creates a virtual environment in `.venv` containing the application along with all its dependencies. The `--frozen` flag makes sure that the exact versions pinned in `uv.lock` are installed.

Then you can start the web application like so:

```
$ uv run pserve development.ini
```

and visit [http://localhost:6543/briefkasten/](http://localhost:6543/briefkasten/). Host and port can be changed in the `[server:main]` section of `development.ini`.

# Customization

The briefkasten application deliberately only serves a very minimalistic markup by default. While you could go ahead and fork the project and modify the templates directly, that is not encouraged. Instead we provide a generic 'theming' approach using [Diazo](https://docs.diazo.org/en/latest/), where you simply add static HTML and CSS files which are then applied at runtime to the application's markup.

This means you neither have to learn how the application works in detail nor do you risk accidentally breaking its functionality.

## Changing the default look

To change the default look you need to do three things:

- create a theme directory
- point the application configuration to it
- restart the application

A theme directory must conform to the following structure:

```
rules.xml
theme.html
assets/
```

`rules.xml` must be a valid Diazo rule file, which needs to point to (at least) one HTML template (i.e. `theme.html`). Any files located inside the `assets/` directory can be referenced from the theme, so you can add any images, CSS, JS and whatnot there. It's best to reference those assets with relative paths, that way you can develop the theme simply by opening the theme HTML file in a browser.

For further information on how to create additional rules see the [official Diazo documentation](https://docs.diazo.org/en/latest/basic.html).

The application ships with two example themes in `application/themes/`: `default` and `fileuploader`. They are a good starting point for your own theme.

To use a theme, adjust the following two settings in `development.ini`:

```
[app:assets]
use = egg:Paste#static
document_root = themes/mytheme/assets

[filter:theme]
use = egg:diazo
rules = themes/mytheme/rules.xml
debug = true
```

`document_root` points to the `assets/` directory of your theme and `rules` to its `rules.xml`. Both paths may be absolute or relative to the location of `development.ini`.

You then need to restart the application, i.e. by hitting `CTRL-c` in the foreground process and re-running `uv run pserve development.ini`.

Once you've performed these steps you can keep the server running while you're developing the theme, because in debug mode changes to the theme and the rules are picked up instantly without requiring a restart.

# Development

The 'briefkasten' web application is developed in Python 3 as a [Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/latest/) application. Its dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

## Testing

Tests are run using [pytest](https://docs.pytest.org/) like so:

```
$ uv run pytest
```

This outputs a text based coverage report and additionally generates an HTML report in `htmlcov/index.html` where you can browse the code and see which lines are not covered.

Alternatively, the tests can be run via [tox](https://tox.wiki/), which uses `uv` internally:

```
$ tox
```

If you don't want to install GnuPG locally, you can also run the tests inside a container from the root of the repository:

```
$ docker compose -f testing.yaml run --rm backend
```

## Command line tools

Besides the web application the package provides the following commands, which are used on the server to process submissions:

- `worker` – watches the submission queue and processes new submissions (i.e. hands them to the sanitizing scripts and sends them to the editors)
- `janitor` – checks the editors' PGP keys for (upcoming) expiry and cleans up old submissions
- `debug` – processes a single (or all pending) submission(s) in the foreground for debugging purposes

All of them expect the location of the dropbox container directory via `--root` (defaulting to `var/drop_root/`) and can be run locally via `uv run`, i.e.:

```
$ uv run janitor --root var/drop_root/
```

## Code checks

The repository contains a [lefthook](https://lefthook.dev) configuration (`.lefthook.yaml`) which runs [ruff](https://docs.astral.sh/ruff/), `yamllint` and an EditorConfig check on staged files before each commit. `ruff` and the EditorConfig check are run via `uvx`, while `yamllint` needs to be available on the `PATH` (i.e. via `uv tool install yamllint`). To enable the git hooks, run the following in the root of the repository:

```
$ uvx lefthook install
```
