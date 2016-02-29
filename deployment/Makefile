build = true

bin/devpi bin/ploy: bin/pip
	bin/pip install -r requirements.txt

bin/python bin/pip:
	virtualenv --clear -p python2.7 .
	bin/pip install --upgrade setuptools pip

bootstrap:
	bin/ploy bootstrap briefkasten

configure-host:
	bin/ploy configure briefkasten

start-jails:
	bin/ploy start worker
	bin/ploy start webserver
	bin/ploy start appserver
	bin/ploy start cleanser

configure-jails:
	bin/ploy playbook main.yml

upload-pgp-keys:
	bin/ploy do appserver upload_pgp_keys

reset-host:
	bin/ploy do briefkasten reset_jails

update-app:
	bin/ploy do worker update_backend build=$(build)
	bin/ploy do appserver update_backend build=false

update-theme:
	bin/ploy do appserver upload_theme

clean:
	git clean -fXd

.PHONY: clean start-jails bootstrap configure-host configure-jails update-theme
