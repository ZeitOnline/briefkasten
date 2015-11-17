pyversion = 2.7
python = python$(pyversion)

all: bin/pserve

tests: bin/py.test
	@bin/py.test

bin/pserve bin/py.test bin/devpi: bin/python bin/pip setup.py
	bin/python setup.py dev
	@touch $@

bin/python bin/pip:
	virtualenv .
	bin/pip install -U pip setuptools

clean:
	git clean -fXd

.PHONY: all $(cfgs) clean
