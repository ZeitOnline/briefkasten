PROJECT := briefkasten_watchdog

MOUNT_SOURCE := --volume $(CURDIR)/src/watchdog:/src

.PHONY: develop
develop: develop-container
	docker run --rm -it $(MOUNT_SOURCE) $(PROJECT):develop


.PHONY: develop-container
develop-container: 
	docker build --quiet --target develop --tag $(PROJECT):develop $(CURDIR)


pyversion = 2.7
python = python$(pyversion)

bin/watchdog: requirements.txt bin/pip
	bin/pip install -r requirements.txt
	@touch $@

bin/devpi: bin/python bin/pip src/watchdog/setup.py bin/watchdog
	bin/python src/watchdog/setup.py dev
	@touch $@

upload: setup.py bin/devpi
	PATH=${PWD}/bin:${PATH} bin/devpi upload --no-vcs src/watchdog 

bin/python bin/pip:
	virtualenv .
	bin/pip install -U pip setuptools

clean:
	git clean -fXd

.PHONY: clean upload

