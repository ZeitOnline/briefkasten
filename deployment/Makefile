build = true
use_pypi = false

default:
	@echo Please explicitly select one of the targets.

bootstrap:
	ploy bootstrap briefkasten

configure-host:
	ploy configure briefkasten

start-jails:
	ploy start briefkasten-worker
	ploy start briefkasten-webserver
	ploy start briefkasten-appserver
	ploy start briefkasten-cleanser

configure-jails:
	ploy playbook main.yml

upload-pgp-keys:
	ploy do briefkasten-worker upload_pgp_keys
	ploy playbook main.yml -t update-config -t update-pgp

reset-host:
	ploy do briefkasten reset_jails

login-devpi:
	ploy do briefkasten-appserver login_devpi user=briefkasten

update-app:
	ploy do briefkasten-worker update_backend build=$(build) use_pypi=$(use_pypi)
	ploy do briefkasten-appserver update_backend build=false use_pypi=$(use_pypi)

update-theme:
	ploy do briefkasten-appserver upload_theme

update-config:
	ploy playbook main.yml -t update-config -t update-pgp

clean:
	git clean -fXd

.PHONY: clean start-jails bootstrap configure-host configure-jails update-theme
