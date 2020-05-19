pyversion = 3
python = python$(pyversion)

venv/bin/devpi venv/bin/pip venv/bin/watchdog: src/watchdog/setup.py
	tox -e develop --notest

upload: setup.py venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs src/watchdog 

clean:
	git clean -fXd

.PHONY: clean upload

