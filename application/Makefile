pyversion = 2.7
python = python$(pyversion)

tests:
	tox

venv/bin/devpi venv/bin/python: setup.py 
	tox -e develop --notest

upload: setup.py venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs

clean:
	git clean -fXd

.PHONY: all $(cfgs) clean tests upload
