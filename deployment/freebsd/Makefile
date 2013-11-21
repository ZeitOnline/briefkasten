bin/ansible: src/ansible/setup.py bin/pip library/ezjail
	bin/pip install -e src/ansible
	echo "You *must* source src/ansible/hacking/env-setup *and* source/bin/activate."

library/ezjail: src/ezjailansible/ezjail.py
	ln -s ../src/ezjailansible/ezjail.py library/ezjail

src/ansible/setup.py: bin/buildout
	bin/buildout

bin/buildout: bin/pip
	bin/pip install zc.buildout

bin/python bin/pip:
	virtualenv .

clean:
	git clean -fXd

.PHONY: clean
