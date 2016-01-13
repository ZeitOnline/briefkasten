pyversion = 2.7
python = python$(pyversion)

all: bin/tox

tests: bin/py.test
	@bin/py.test

bin/pserve: requirements.txt bin/pip
	bin/pip install -r requirements.txt
	@touch $@

bin/tox bin/py.test bin/devpi: bin/python bin/pip setup.py bin/pserve
	bin/python setup.py dev
	@touch $@

upload: setup.py bin/py.test bin/devpi
	PATH=${PWD}/bin:${PATH} bin/devpi upload --no-vcs

bin/python bin/pip:
	virtualenv .
	bin/pip install -U pip setuptools

clean:
	git clean -fXd

.PHONY: all $(cfgs) clean tests upload
