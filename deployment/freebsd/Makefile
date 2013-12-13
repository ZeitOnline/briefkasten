passphrase = 

bin/ansible:  bin/pip
	bin/pip install ansible

bin/python bin/pip:
	virtualenv .

library/ezjail: src/ezjailansible/ezjail.py
	ln -s ../src/ezjailansible/ezjail.py library/ezjail

bootstrap0:
	bin/ansible-playbook -i host bootstrap0.yml -k -c paramiko

bootstrap1:
	bin/ansible-playbook -i host bootstrap1.yml --extra-vars "geli_passphrase=$(passphrase)"

cert: roles/webserver/files/briefkasten.crt, roles/webserver/files/briefkasten.key

roles/webserver/files/briefkasten.crt, roles/webserver/files/briefkasten.key:
	openssl req -x509 -newkey rsa:2048 -keyout roles/webserver/files/briefkasten.key -out roles/webserver/files/briefkasten.crt -days 365 -nodes

deploy:
	bin/ansible-playbook -i host site.yml

mount_geli:
	bin/ansible-playbook -i host bootstrap1.yml -t mount_geli --extra-vars "geli_passphrase=$(passphrase)"

clean:
	git clean -fXd

.PHONY: clean bootstrap0 bootstrap1 deploy mount_geli

