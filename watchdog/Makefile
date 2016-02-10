pyversion = 2.7
python = python$(pyversion)

bin/watchdog: requirements.txt bin/pip
	bin/pip install -r requirements.txt
	@touch $@

bin/devpi: bin/python bin/pip setup.py bin/watchdog
	bin/python setup.py dev
	@touch $@

upload: setup.py bin/devpi
	PATH=${PWD}/bin:${PATH} bin/devpi upload --no-vcs

bin/python bin/pip:
	virtualenv .
	bin/pip install -U pip setuptools

clean:
	git clean -fXd

.PHONY: clean upload

