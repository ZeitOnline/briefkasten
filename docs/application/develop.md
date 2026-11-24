# Entwicklung

Die Webanwendung `briefkasten` ist eine [Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/latest/)-Anwendung in Python 3.
Die Abhängigkeiten werden mit [uv](https://docs.astral.sh/uv/) verwaltet, die Tests laufen mit [pytest](https://docs.pytest.org/) (über [tox](https://tox.wiki/)).

Der Code der Anwendung liegt im Verzeichnis `application/` des Repositorys:

```
application/
├── briefkasten/          # das Python-Paket (Views, Drop-Verarbeitung, Kommandos, Templates, Tests)
├── development.ini      # Paste-/Pyramid-Konfiguration für die lokale Entwicklung
├── middleware_scripts/  # Shell-Skripte, die in Produktion die Anhänge bereinigen
├── themes/              # Diazo-Themes (`default` und `fileuploader`)
├── var/drop_root/       # lokaler Dropbox-Container inkl. seiner `settings.yaml`
├── pyproject.toml       # Paket-Metadaten, Abhängigkeiten, Konfiguration von pytest und ruff
├── tox.ini
└── uv.lock
```

## Voraussetzungen

- Python ≥ 3.12 (das Docker-Image verwendet Python 3.14)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [GnuPG](https://gnupg.org/) (`gpg`), wird zum Verschlüsseln der Drops und von der Testsuite benötigt

Die Skripte, die in Produktion die Anhänge tatsächlich bereinigen (`middleware_scripts/`), brauchen weitere Werkzeuge (LibreOffice, ImageMagick usw.).
Für die Entwicklung der Webanwendung oder eines Themes sind sie nicht nötig: Lokal wird stattdessen ein Mock-Skript verwendet (siehe [Verarbeitung der Drops](#verarbeitung-der-drops)).

## Einrichtung

```
$ cd application
$ uv sync
```

Das legt in `application/.venv` ein virtualenv an, in dem die Anwendung samt Entwicklungsabhängigkeiten installiert ist.

## Webanwendung starten

```
$ uv run pserve development.ini
```

Danach ist die Anwendung unter [http://localhost:6543/briefkasten/](http://localhost:6543/briefkasten/) erreichbar.

`development.ini` hängt die Anwendung unter `/briefkasten/` ein (`appserver_root_url`) und legt das Diazo-Theme `fileuploader` darüber.
Änderungen an Templates werden ohne Neustart übernommen (`pyramid.reload_templates = true`).

Die Anwendung stellt folgende Routen bereit (relativ zu `appserver_root_url`):

| Route | Methode | Zweck |
|---|---|---|
| `/briefkasten/` | GET | das Einreichungsformular mit einem signierten, kurzlebigen Post-Token |
| `/briefkasten/{token}/upload` | POST | asynchroner Datei-Upload (JSON, wird vom JavaScript-Uploader genutzt) |
| `/briefkasten/{token}/submit` | POST | Formular absenden; leitet auf die Rückmeldeseite weiter |
| `/briefkasten/dropbox/{drop_id}` | GET | Rückmeldeseite für die einreichende Person, zeigt Antworten der Redaktion |
| `/briefkasten/dropbox/{drop_id}/{editor_token}` | GET, POST | Seite für die Redaktion, um den Status zu sehen und zu antworten |
| `/metrics` | GET | Prometheus-Metriken, die das Kommando `janitor` schreibt |

Das Post-Token läuft nach `post_token_max_age_seconds` ab (Standard: 300 Sekunden); wird ein abgelaufenes Formular abgeschickt, antwortet die Anwendung mit `410 Gone`.

## Verarbeitung der Drops

Die Webanwendung speichert eine Einreichung („Drop“) nur auf der Festplatte und markiert sie als `020 submitted`, indem sie im Verzeichnis `submissions/` des Dropbox-Containers (`fs_dropbox_root`, lokal `var/drop_root/`) eine Datei anlegt.
Alles Weitere passiert in einem separaten Prozess, der als Konsolenskript mit dem Paket installiert wird:

| Kommando | Zweck |
|---|---|
| `uv run worker [--root DIR] [--async/--no-async]` | beobachtet `submissions/` und verarbeitet neue Drops; Drops mit Anhängen werden in einem Pool aus `num_workers` Prozessen verarbeitet |
| `uv run debug [--root DIR] [DROP_ID]` | verarbeitet einen einzelnen Drop (oder alle Drops im Status `020`) im Vordergrund, hilfreich zum Debuggen |
| `uv run janitor [--root DIR]` | prüft die PGP-Schlüssel der Redaktion, löscht Drops, deren Status sich seit mehr als 365 Tagen nicht geändert hat (Watchdog-Drops nach einem Tag), und schreibt die Datei `metrics`, die unter `/metrics` ausgeliefert wird |

`--root` ist standardmäßig `var/drop_root/`.

Die Verarbeitung eines Drops läuft so ab:

1. Wenn es Anhänge gibt, wird zuerst ein verschlüsseltes Backup der Originaldateien angelegt und dann `process-attachments.sh` aus `fs_bin_path` aufgerufen, um sie zu bereinigen.
   Die lokale `settings.yaml` lässt `fs_bin_path` auf `briefkasten/tests/bin/` zeigen; dort liegt ein Mock, der die Dateien unverändert verschiebt.
2. Die Nachricht (und die bereinigten Anhänge, sofern sie kleiner als `attachment_size_threshold` sind) werden für jedes Redaktionsmitglied verschlüsselt und per E-Mail verschickt.
3. Bis auf die Statusdatei, das Editor-Token und Antworten der Redaktion werden alle Daten aus dem Drop gelöscht.

Damit Schritt 2 lokal funktioniert, braucht man:

- die öffentlichen Schlüssel aller `editors` im Keyring aus `fs_pgp_pubkeys` (lokal `~/.gnupg/`); Redaktionsmitglieder ohne Schlüssel werden übersprungen,
- einen SMTP-Server unter `mail.host`/`mail.port` (lokal `localhost:8025`), der `STARTTLS` unterstützt.

Andernfalls landet der Drop in einem `6xx`-Status (z. B. `610 smtp error`), der sich in `var/drop_root/drops/<drop_id>/status` nachlesen lässt.

Alle Einstellungen sind unter [Konfiguration](configuration.md) beschrieben.

## Anpassung

Die Anwendung liefert bewusst nur minimales Markup aus.
Statt ihre Templates zu ändern, wird das Aussehen mit [Diazo](https://docs.diazo.org/en/latest/) angepasst: Man liefert statisches HTML und CSS, und Diazo wendet es zur Laufzeit auf das Markup der Anwendung an.
So muss man weder im Detail verstehen, wie die Anwendung funktioniert, noch riskiert man, versehentlich ihre Funktionalität zu beschädigen.

### Eigenes Theme

Ein Theme ist ein Verzeichnis mit folgender Struktur (zwei Beispiele liegen in `application/themes/`):

```
rules.xml
default.html
assets/
```

`rules.xml` muss gültige [Diazo-Regeln](https://docs.diazo.org/en/latest/basic.html) enthalten und über `<theme href="…"/>` auf (mindestens) ein HTML-Template verweisen.
Dateien in `assets/` können aus dem Theme referenziert werden, dort lassen sich also Bilder, CSS, JS usw. ablegen.
Am besten referenziert man sie mit relativen Pfaden; dann kann man das Theme entwickeln, indem man die HTML-Datei einfach im Browser öffnet.

Das Theme wird in `development.ini` konfiguriert:

```
[app:assets]
use = egg:Paste#static
document_root = themes/mycustomtheme/assets

[filter:theme]
use = egg:diazo
rules = themes/mycustomtheme/rules.xml
debug = true
```

Die App `assets` ist im Abschnitt `[composite:main]` unter `/briefkasten/assets` eingehängt.
Nach einer Änderung an `development.ini` muss `pserve` neu gestartet werden; mit `debug = true` werden weitere Änderungen am Theme und an den Regeln danach ohne Neustart übernommen.

### Templates ersetzen

Reicht Diazo nicht aus, kann ein Python-Paket mit einem Verzeichnis `templates/` die Templates der Anwendung ersetzen.
Dazu `theme_package` auf den Namen dieses Pakets setzen; es muss alle Templates aus `briefkasten/templates/` bereitstellen (die Chameleon-Templates `.pt` für die Webseiten und `editor_email.j2` für die E-Mail an die Redaktion).
Die Einstellung wird an zwei Stellen gelesen: aus der `.ini`-Datei für die Webseiten und aus der `settings.yaml` des Dropbox-Containers für die E-Mail. Sie muss deshalb an beiden Stellen gesetzt werden.

## Tests

Im Wurzelverzeichnis des Repositorys

```
$ bin/test
```

ausführen. Das startet `tox` in `application/`; Argumente werden an pytest durchgereicht, z. B. `bin/test -k editor`.
Alternativ pytest direkt aufrufen:

```
$ cd application
$ uv run pytest briefkasten/tests
```

Jeder Lauf gibt einen Coverage-Bericht im Terminal aus und schreibt einen HTML-Bericht nach `application/htmlcov/index.html`.

Die Tests verwenden den GPG-Keyring in `briefkasten/tests/gpghome/` und die Mock-Skripte in `briefkasten/tests/bin/`, brauchen also keine externen Dienste.

Auf GitHub laufen die Tests in Docker: Die CI baut die Stage `backend-testing` aus dem `Dockerfile` (siehe `testing.yaml`), deren Entrypoint `tox` ist.

## Linting

Die Linter laufen als Pre-Commit-Hook über [lefthook](https://lefthook.dev/) (`.lefthook.yaml`) und im Workflow `Backend CI`:

- [editorconfig-checker](https://editorconfig-checker.github.io/)
- [ruff](https://docs.astral.sh/ruff/) für Python (konfiguriert in `application/pyproject.toml`)
- [yamllint](https://yamllint.readthedocs.io/) für YAML-Dateien

Den Hook mit `lefthook install` installieren oder ruff von Hand aufrufen:

```
$ cd application
$ uvx ruff check
```

## Releases

Releases erstellt [release-please](https://github.com/googleapis/release-please) aus den [Conventional Commits](https://www.conventionalcommits.org/) auf `main`; dabei werden auch die Version in `application/pyproject.toml` und das `CHANGELOG.md` aktualisiert.

## Dokumentation

Diese Dokumentation liegt in `docs/` und wird mit MkDocs gebaut.
Für eine lokale Vorschau:

```
$ bin/docs serve
```

und [http://localhost:8000](http://localhost:8000) öffnen.
