build = true
use_pypi = false

bin/devpi bin/ploy: bin/pip
	bin/pip install -r requirements.txt

bin/python bin/pip:
	virtualenv --clear -p python2.7 .
	bin/pip install --upgrade setuptools pip

bootstrap: bin/ploy
	bin/ploy bootstrap briefkasten

configure-host:
	bin/ploy configure briefkasten

start-jails:
	bin/ploy start briefkasten-worker
	bin/ploy start briefkasten-webserver
	bin/ploy start briefkasten-appserver
	bin/ploy start briefkasten-cleanser

configure-jails:
	bin/ploy playbook main.yml

upload-pgp-keys:
	bin/ploy do worker upload_pgp_keys
	bin/ploy configure worker -t update-pgp

reset-host:
	bin/ploy do briefkasten reset_jails

update-app:
	bin/ploy do worker update_backend build=$(build) use_pypi=$(use_pypi)
	bin/ploy do appserver update_backend build=false use_pypi=$(use_pypi)

update-theme:
	bin/ploy do appserver upload_theme

clean:
	git clean -fXd

.PHONY: clean start-jails bootstrap configure-host configure-jails update-theme
