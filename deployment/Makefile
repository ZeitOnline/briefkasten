build = true
use_pypi = false

venv/bin/devpi venv/bin/ploy: venv/bin/pip
	venv/bin/pip install -r requirements.txt

venv/bin/python venv/bin/pip:
	tox -e develop --notest

bootstrap: venv/bin/ploy
	venv/bin/ploy bootstrap briefkasten

configure-host: venv/bin/ploy
	venv/bin/ploy configure briefkasten

start-jails: venv/bin/ploy
	venv/bin/ploy start briefkasten-worker
	venv/bin/ploy start briefkasten-webserver
	venv/bin/ploy start briefkasten-appserver
	venv/bin/ploy start briefkasten-cleanser

configure-jails:
	venv/bin/ploy playbook main.yml

upload-pgp-keys: venv/bin/ploy
	venv/bin/ploy do briefkasten-worker upload_pgp_keys
	venv/bin/ploy playbook main.yml -t update-config -t update-pgp

reset-host: venv/bin/ploy
	venv/bin/ploy do briefkasten reset_jails

login-devpi: venv/bin/ploy
	venv/bin/ploy do briefkasten-appserver login_devpi user=briefkasten

update-app: venv/bin/ploy
	venv/bin/ploy do briefkasten-worker update_backend build=$(build) use_pypi=$(use_pypi)
	venv/bin/ploy do briefkasten-appserver update_backend build=false use_pypi=$(use_pypi)

update-theme: venv/bin/ploy
	venv/bin/ploy do briefkasten-appserver upload_theme

update-config: venv/bin/ploy
	venv/bin/ploy playbook main.yml -t update-config -t update-pgp

clean:
	git clean -fXd

.PHONY: clean start-jails bootstrap configure-host configure-jails update-theme
