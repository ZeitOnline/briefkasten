bin/devpi bin/ploy: bin/pip
	bin/pip install -r requirements.txt

bin/python bin/pip:
	virtualenv --clear -p python2.7 .
	bin/pip install --upgrade setuptools pip

clean:
	git clean -fXd

.PHONY: clean 
