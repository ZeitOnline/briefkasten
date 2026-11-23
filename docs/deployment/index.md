# Deployment

Wir könnten einfach fertige Installations-Images bereitstellen. Das würde aber der Idee widersprechen, eine vertrauenswürdige Open-Source-Dropbox zu betreiben: Man selbst und die einreichenden Personen müssten diesen Binaries dann blind vertrauen, ohne ihre Integrität prüfen zu können.

Stattdessen werden so wenige vorgefertigte Bestandteile wie möglich verwendet und aus vertrauenswürdigen Quellen bezogen (den offiziellen FreeBSD-Repositorys). Im Grunde bekommt man eine Einkaufsliste mit Zutaten und ein Rezept und kocht selbst, statt ein Fertiggericht serviert zu bekommen.

Eine Briefkasten-Instanz wird deployt, indem man auf einem *Control Host* (dem eigenen Rechner) Kommandos ausführt, die einen *Target Host* installieren und konfigurieren (eine virtuelle Maschine für Tests oder eigene Hardware für die Produktion).
Dazu bootet der *Target Host* zunächst ein [mfsBSD](https://mfsbsd.vx.sk)-Image, wird dann remote mit FreeBSD installiert und anschließend mit [ploy](https://github.com/ployground/ploy), [bsdploy](https://github.com/ployground/bsdploy), Ansible und Fabric eingerichtet.
Alle Dateien dafür liegen im Verzeichnis `deployment/` des Repositorys.

## Aufbau

Auf dem *Target Host* (FreeBSD 15.1, ZFS-Pool `tank`, verschlüsselt mit GELI) laufen mehrere [ezjail](https://erdgeist.org/arts/software/ezjail/)-Jails:

| Jail | IP | Aufgabe |
|---|---|---|
| `webserver` | 10.0.0.1 | nginx; terminiert HTTPS und leitet `approot_url` und `/metrics` an den Appserver weiter |
| `appserver` | 10.0.0.2 | die Webanwendung (`pserve`, Port 6543), nimmt Einreichungen entgegen |
| `cleanser` | 10.0.0.3 | Vorlage für die Cleanser-Jails `cleanser_01` … `cleanser_05`, die die Anhänge bereinigen |
| `worker` | 10.0.0.4 | der `worker` aus der Anwendung: verschlüsselt die Drops, lässt sie bereinigen und verschickt die E-Mails; außerdem läuft hier täglich der `janitor` |

Appserver und Worker teilen sich das ZFS-Dataset `tank/data/briefkasten`, das in beiden Jails unter `/var/briefkasten` eingehängt ist (Dropbox-Container in `/var/briefkasten/drop_root`, PGP-Schlüssel in `/var/briefkasten/pgp_pubkeys`).

Die Cleanser-Jails sind ZFS-Klone der Jail `cleanser`. Das Werkzeug `jdispatch` auf dem Host teilt dem Worker für jeden Drop eine freie Cleanser-Jail zu und setzt sie nach der Benutzung (oder nach `cleanser_timeout_secs`) auf einen sauberen Snapshot zurück. Wie ein Drop dabei durchlaufen wird, steht unter [Der Lebenszyklus einer Einreichung](../application/workings.md).

## Kurzfassung

Im Verzeichnis `deployment/`:

1. `uv sync`
2. `etc/` befüllen: `ploy.conf`, PGP-Schlüssel in `etc/pgp_pubkeys/`, `briefkasten.crt` und `briefkasten.key` (siehe [Setup konfigurieren](#setup-konfigurieren))
3. den *Target Host* in mfsBSD booten (bei VirtualBox: `uv run ploy -c etc/ploy.conf start briefkasten-vbox`)
4. `uv run make bootstrap`, danach den SSH-Fingerprint in `etc/ploy.conf` eintragen
5. `uv run make configure-host`
6. `uv run make start-jails`
7. `uv run make configure-jails`
8. `uv run make upload-pgp-keys`

## Voraussetzungen auf dem Control Host

- Python 3.12 (`deployment/pyproject.toml` verlangt `>=3.12,<3.13`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- `make`, `rsync` und `ssh`
- für Tests auf einer lokalen VM: [VirtualBox](https://www.virtualbox.org) mit den Kommandozeilenwerkzeugen im `PATH`

Quellcode holen und die Deployment-Werkzeuge installieren:

```
$ git clone https://github.com/ZeitOnline/briefkasten.git
$ cd briefkasten/deployment
$ uv sync
```

`uv sync` legt in `deployment/.venv` ein virtualenv mit ploy, bsdploy, ploy_ansible und Ansible an (teils aus Git-Forks, siehe `[tool.uv.sources]` in `pyproject.toml`).
Alle `make`-Targets rufen `ploy` auf und werden deshalb mit `uv run make …` ausgeführt (oder nach `source .venv/bin/activate` mit `make …`).

Die `make`-Targets verwenden standardmäßig `etc/ploy.conf`. Eine andere Konfiguration lässt sich mit `config=` auswählen, z. B. `uv run make configure-host config=etc/staging.conf`. Das funktioniert bei allen Targets außer bei Schritten, die `ploy-ssh` benutzen – etwa dem Theme-Upload in `configure-jails`, der immer `etc/ploy.conf` verwendet.

## Setup konfigurieren

Alles, was ein konkretes Setup von einem generischen unterscheidet, liegt in `deployment/etc/`. Das Verzeichnis ist von Git ausgeschlossen; es empfiehlt sich, es separat zu versionieren. Ein guter Start ist eine Kopie von `etc.sample`:

```
$ cp -R etc.sample etc
```

### ploy.conf

`etc.sample` enthält zwei Vorlagen:

- `plain.conf` für einen bestehenden Host (Produktion),
- `vbox.conf` für eine lokale VirtualBox-VM.

Die passende Vorlage nach `etc/ploy.conf` kopieren. Beide erweitern `deployment/base.conf`, das die Standardwerte enthält und dessen Kommentare die Optionen ausführlich beschreiben.

!!! warning "Abweichungen in den Vorlagen"
    - Die Vorlagen setzen `ansible-fqdn`. Schlüssel mit dem Präfix `ansible-` werden aber als Ansible-Variable ohne `ploy_`-Präfix weitergereicht (hier `fqdn`), während nginx, Let's Encrypt und die Links in den E-Mails `ploy_fqdn` verwenden. Den Hostnamen deshalb als `fqdn = …` setzen.
    - `plain.conf` setzt `local_theme_path = ../application/themes/fileuploader/`. Der Pfad ist relativ zu `etc/`, richtig ist `../../application/themes/fileuploader/`.
    - `post_secret` und `watchdog_imap_recipient` fehlen in `plain.conf` und müssen ergänzt werden; `test_submission_secret` wird nicht verwendet.
    - Der Kommentar in `base.conf` nennt `dropbox_failed_archive_url_format` und `dropbox_failed_archive_path`; die Rollen lesen `dropbox_dirty_archive_url_format` und `dropbox_dirty_archive_path`.

Im Abschnitt `[ez-master:briefkasten]` müssen mindestens gesetzt werden:

- `ip` (und gegebenenfalls `port`) des *Target Hosts*
- `fingerprint` – der SSH-Fingerprint, den `make bootstrap` ausgibt (siehe [Target Host bootstrappen](#target-host-bootstrappen))

Im Abschnitt `[macro:ez-base]` werden die Einstellungen der Anwendung festgelegt. Ploy reicht sie als Ansible-Variablen `ploy_<name>` an die Rollen weiter, die daraus die `briefkasten.ini` des Appservers und die `settings.yaml` des Dropbox-Containers erzeugen (siehe [Konfiguration](../application/configuration.md)):

| Schlüssel | Standard | Beschreibung |
|---|---|---|
| `fqdn` | `briefkasten.virtualbox` | Hostname des Briefkastens; wird für nginx, Let's Encrypt und die Links in den E-Mails verwendet |
| `approot_url` | `/briefkasten/` | URL-Pfad der Anwendung, muss mit `/` enden |
| `editors` | – | Empfänger\*innen der Einreichungen, durch Leerzeichen getrennt; für jede Adresse muss ein PGP-Schlüssel vorhanden sein |
| `admins` | – | Admin-Adressen, durch Leerzeichen getrennt |
| `mail_sender` | – | Absenderadresse der E-Mails |
| `mail_host`, `mail_port` | `localhost`, `25` | SMTP-Server (die Anwendung verwendet immer `STARTTLS`) |
| `mail_user`, `mail_password` | – | SMTP-Zugangsdaten; alternativ `mail_password_file` mit einer von ploy verschlüsselten Datei |
| `post_secret` | – | **Pflicht**; signiert die Formular-Tokens und dient zugleich als Secret für Testeinreichungen des [Watchdogs](monitoring.md) |
| `watchdog_imap_recipient` | – | **Pflicht**; Empfänger der Testeinreichungen des Watchdogs |
| `root_email` | – | Adresse, an die E-Mails an `root` weitergeleitet werden |
| `local_theme_path` | `../../application/themes/default/` | Pfad zum Diazo-Theme auf dem Control Host, relativ zu `etc/`, mit `/` am Ende |
| `theme_name` | `default` | Name des Themes auf dem Server |
| `use_diazo` | `true` | Theme per Diazo anwenden; bei `false` wird nur `theme_package` verwendet |
| `theme_package` | `briefkasten` | Python-Paket mit den Templates, siehe [Templates ersetzen](../application/develop.md#templates-ersetzen) |
| `attachment_size_threshold` | `1Gb` | bereinigte Anhänge bis zu dieser Größe werden per E-Mail verschickt |
| `dropbox_cleansed_archive_url_format`, `dropbox_cleansed_archive_path` | – | Archiv der bereinigten Anhänge, siehe [Konfiguration](../application/configuration.md#drop-verarbeitung-settingsyaml) |
| `dropbox_dirty_archive_url_format`, `dropbox_dirty_archive_path` | – | Archiv der Originalanhänge, wenn die Bereinigung fehlschlägt. **Achtung:** Damit können einreichende Personen unbeabsichtigt Metadaten an die Redaktion weitergeben |
| `cleanser_timeout_secs` | `180` | wie lange eine Bereinigung dauern darf, bevor die Cleanser-Jail zurückgesetzt wird |
| `use_acme` | `false` | Zertifikat über Let's Encrypt beziehen, siehe [SSL-Zertifikat](#ssl-zertifikat-fur-den-webserver) |
| `enable_zabbix`, `zabbix_host` | `false` | Zabbix-Agent auf dem Host installieren (im Abschnitt `[ez-master:briefkasten]`) |

!!! note
    In `base.conf` sind auch `post_token_max_age_seconds` und `drop_ttl_days` dokumentiert. Die Rollen übernehmen `post_token_max_age_seconds` aber nicht in die `briefkasten.ini` (es gilt der Standard von 300 Sekunden), und der `janitor` wertet `drop_ttl_days` nicht aus (Drops werden nach 365 Tagen gelöscht).

Die Anzahl der Cleanser-Jails (`ploy_cleanser_count`, Standard 5) und weitere Werte für den Host stehen in `deployment/group_vars/all.yml`.

### SSH-Schlüssel

Beim Bootstrapping wird ein öffentlicher SSH-Schlüssel als `authorized_keys` für `root` auf dem *Target Host* installiert. bsdploy sucht ihn als Datei `authorized_keys` im Verzeichnis `bootstrap-files` (`etc/bootstrap-files/`, bei `vbox.conf` `deployment/bootstrap-files/vbox/`) und greift sonst auf `~/.ssh/identity.pub`, `~/.ssh/id_rsa.pub`, `~/.ssh/id_dsa.pub` oder `~/.ssh/id_ecdsa.pub` zurück.

### PGP-Schlüssel der Redaktion

Für jede Adresse in `editors` (und `admins`) muss ein öffentlicher PGP-Schlüssel in `etc/pgp_pubkeys/` liegen. `make upload-pgp-keys` lädt alle Dateien aus diesem Verzeichnis in die Worker-Jail und importiert sie dort in den Keyring unter `/var/briefkasten/pgp_pubkeys`. Ob die Schlüssel gültig sind und wann sie ablaufen, prüft der `janitor` (siehe [Monitoring](monitoring.md)).

### SSL-Zertifikat für den Webserver

nginx spricht ausschließlich HTTPS und erwartet Zertifikat und Schlüssel in `etc/briefkasten.crt` und `etc/briefkasten.key`. `etc.sample` enthält ein selbstsigniertes Paar für Entwicklung und Tests.

Läuft der Briefkasten hinter einem Proxy und ist nur über einen Unterpfad wie `/briefkasten/` öffentlich erreichbar, reicht ein selbstsigniertes Paar: Es soll nur den Verkehr zwischen Proxy und Briefkasten verschlüsseln.

Soll der Briefkasten direkt öffentlich erreichbar sein, kann das Zertifikat über Let's Encrypt mit dem Client acme.sh und der [DNS-Alias-Methode](https://github.com/acmesh-official/acme.sh/wiki/DNS-alias-mode) bezogen werden. Dazu in `[macro:ez-base]` setzen:

```
use_acme = true
acme_domain = <die verwendete Alias-Domain>
acme_key = <der Schlüssel, mit dem das DNS-Update signiert wird>
acme_ddns_server = <IP oder Hostname des Nameservers>
```

## Target Host in mfsBSD booten

Statt des offiziellen FreeBSD-Installers wird [mfsBSD](https://mfsbsd.vx.sk) verwendet: Es konfiguriert das Netzwerk per DHCP und erlaubt SSH-Logins als `root` mit dem Passwort `mfsroot`. Von dort installiert bsdploy FreeBSD 15.1 (`ezjail-install-release` und `bootstrap-bsd-url` in `base.conf`).

### Mit VirtualBox

Für Tests und Entwicklung, da es sich vollständig automatisieren lässt. Mit `etc/ploy.conf` als Kopie von `vbox.conf`:

```
$ uv run ploy -c etc/ploy.conf start briefkasten-vbox
```

Das lädt das mfsBSD-ISO herunter, legt eine VM an und bootet sie. Die VM ist per SSH über `127.0.0.1:47030` erreichbar und bekommt im Host-only-Netz die Adresse `192.168.56.160` (siehe `bootstrap-files/vbox/rc.conf`). Weiter mit [Target Host bootstrappen](#target-host-bootstrappen).

### Auf eigener Hardware

Für die Produktion. Die Maschine braucht mindestens 2 GB RAM und 10 GB Festplatte.

1. Ein aktuelles mfsBSD-Image samt Prüfsummen von [mfsbsd.vx.sk](https://mfsbsd.vx.sk) herunterladen und mit `shasum` prüfen.
2. Das Image auf einen USB-Stick schreiben (unter macOS: Gerät mit `diskutil list` ermitteln, `diskutil unmountDisk /dev/diskN`, dann `sudo dd if=<image> of=/dev/diskN bs=1m`).
3. Den *Target Host* vom Stick booten und als `root` mit dem Passwort `mfsroot` anmelden.
4. Mit `ifconfig` die IP-Adresse ermitteln (ohne DHCP in `/etc/rc.conf` setzen) und mit `gpart list` die Festplatten. Die IP-Adresse in `etc/ploy.conf` eintragen; die Festplatten stehen als `root_devices` in `group_vars/all.yml`.

## Target Host bootstrappen

```
$ uv run make bootstrap
```

installiert FreeBSD auf den *Target Host*. Die Rückfragen mit `y` beantworten; danach startet der Host neu.
Am Ende gibt das Skript den Fingerprint des neuen SSH-Daemons aus. Dieser **muss** im Abschnitt `[ez-master:briefkasten]` als `fingerprint = …` eingetragen werden.

Sobald der Host neu gestartet ist:

```
$ uv run make configure-host
```

Das richtet den Jail-Host ein (ZFS-Datasets, ezjail, Weiterleitung der `root`-E-Mails).

## Jails installieren

```
$ uv run make start-jails
$ uv run make configure-jails
$ uv run make upload-pgp-keys
```

- `start-jails` legt die Jails `worker`, `webserver`, `appserver` und `cleanser` an und startet sie.
- `configure-jails` führt das Playbook `main.yml` aus: Es installiert die Anwendung mit uv aus `application/pyproject.toml` und `application/uv.lock`, konfiguriert nginx, supervisord, Worker und Appserver, lädt das Theme hoch, erzeugt die Cleanser-Klone und richtet `jdispatch` ein.
- `upload-pgp-keys` importiert die Schlüssel der Redaktion und aktualisiert die Konfiguration.

## Installation testen

Der Briefkasten ist jetzt unter `https://<fqdn><approot_url>` erreichbar, bei VirtualBox unter [https://192.168.56.160/briefkasten/](https://192.168.56.160/briefkasten/).

Klappt das bei VirtualBox nicht, die tatsächliche Adresse der VM ermitteln:

```
$ uv run ploy -c etc/ploy.conf ssh briefkasten 'ifconfig em0'
```

und die Adresse aus der Zeile `inet` verwenden.

Auf der Seite einen Text eingeben, einen oder mehrere Anhänge hinzufügen und das Formular abschicken. Es sollte eine Erfolgsmeldung mit einem Link zur Rückmeldeseite erscheinen. Jede Adresse aus `editors` sollte eine verschlüsselte E-Mail mit dem Text und den bereinigten Anhängen erhalten (ein Word-Dokument z. B. als PDF).

## Aktualisieren und Betrieb

| Kommando | Zweck |
|---|---|
| `uv run make update-config` | `briefkasten.ini` und `settings.yaml` nach Änderungen an `ploy.conf` neu erzeugen und die Dienste neu starten |
| `uv run make upload-pgp-keys` | neue oder geänderte PGP-Schlüssel hochladen |
| `uv run make update-theme` | das Theme aus `local_theme_path` erneut hochladen und den Appserver neu starten |
| `uv run make update-app` | die Anwendung aus dem devpi-Index `briefkasten/dev` (`default_publish_devpi`) neu installieren; mit `build=true` (Standard) wird sie vorher lokal gebaut und hochgeladen, mit `use_pypi=true` von PyPI installiert |
| `uv run make login-devpi` | am devpi-Server anmelden (für `update-app`) |
| `uv run make reset-host` | **löscht** alle Jails und Cleanser-Klone, um sie neu aufzusetzen (mit Rückfrage) |

Webanwendung und Worker laufen unter supervisord (`briefkasten_frontend` und `briefkasten_worker`). Die Ausgabe des Workers landet in `/var/briefkasten/log/` der Worker-Jail; die Webanwendung protokolliert nichts.
