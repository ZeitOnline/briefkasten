# Konfiguration

Die Anwendung liest ihre Konfiguration aus zwei Quellen:

- der **`.ini`-Datei**, die `pserve` übergeben wird (lokal `application/development.ini`); sie konfiguriert die Webanwendung, und
- der **`settings.yaml`** im Verzeichnis des Dropbox-Containers (lokal `application/var/drop_root/settings.yaml`); sie legt fest, wie Drops verarbeitet werden. Sie wird sowohl von der Webanwendung als auch von den Kommandos `worker`, `debug` und `janitor` gelesen.

Im Deployment werden beide Dateien von Ansible aus der `ploy.conf` erzeugt (`/usr/local/briefkasten/briefkasten.ini` im Appserver, `/var/briefkasten/drop_root/settings.yaml` im Worker); welche Schlüssel dort welche Einstellung setzen, steht unter [Deployment](../deployment/index.md#ployconf).

## Webanwendung (`.ini`)

Diese Schlüssel gehören in den Abschnitt `[app:briefkasten]`:

| Schlüssel | Pflicht | Standard | Beschreibung |
|---|---|---|---|
| `fs_dropbox_root` | ja | | Pfad des Dropbox-Containers (des Verzeichnisses mit der `settings.yaml`) |
| `post_secret` | ja | | Secret, mit dem die Post-Tokens im Einreichungsformular signiert werden |
| `post_token_max_age_seconds` | nein | `300` | wie lange ein Post-Token (also ein geladenes Formular) gültig bleibt |
| `appserver_root_url` | nein | `/` | URL-Präfix aller Routen; **muss** mit einem Schrägstrich enden |
| `theme_package` | nein | `briefkasten` | Python-Paket, das die Seiten-Templates bereitstellt, siehe [Templates ersetzen](develop.md#templates-ersetzen) |

Daneben gelten die üblichen `pyramid.*`-Einstellungen (z. B. `pyramid.reload_templates`).
Andere Schlüssel in diesem Abschnitt – etwa `fs_bin_path` in `development.ini` oder `fs_pgp_pubkeys` und `test_submission_secret` in der `briefkasten.ini` des Deployments – haben keine Wirkung; diese Werte liest die Anwendung nur aus der `settings.yaml`.
Die übrigen Abschnitte von `development.ini` richten das Diazo-Theme, die statischen Assets und den lokalen HTTP-Server ein, siehe [Eigenes Theme](develop.md#eigenes-theme).

## Drop-Verarbeitung (`settings.yaml`)

| Schlüssel | Pflicht | Standard | Beschreibung |
|---|---|---|---|
| `editors` | ja | | Liste der E-Mail-Adressen, die Einreichungen erhalten; zu jeder muss ein öffentlicher Schlüssel in `fs_pgp_pubkeys` liegen |
| `admins` | ja | | Liste der E-Mail-Adressen der Admins; wird von der Anwendung eingelesen, aber derzeit nicht verwendet |
| `fs_pgp_pubkeys` | ja | | GnuPG-Home-Verzeichnis mit den öffentlichen Schlüsseln der Redaktion |
| `fs_gpg_path` | nein | `gpg` | Pfad zum `gpg`-Binary |
| `fs_bin_path` | ja¹ | | Verzeichnis mit `process-attachments.sh` und dessen `briefkasten.conf` |
| `attachment_size_threshold` | nein | `2Mb` | bereinigte Anhänge bis zu dieser Gesamtgröße werden per E-Mail verschickt, größere nur als verschlüsseltes Archiv |
| `dropbox_view_url_format` | ja | | URL der Rückmeldeseite für die einreichende Person, `%s` wird durch die Drop-ID ersetzt |
| `dropbox_editor_url_format` | ja | | URL der Redaktionsseite, die beiden `%s` werden durch Drop-ID und Editor-Token ersetzt |
| `dropbox_cleansed_archive_url_format` | nein | | URL, unter der die Redaktion das verschlüsselte Archiv der bereinigten Anhänge herunterladen kann (`%s`: Drop-ID) |
| `dropbox_dirty_archive_url_format` | nein | | URL des verschlüsselten Archivs der Originalanhänge (`%s`: Drop-ID); ist sie gesetzt, wird dieses Archiv aufbewahrt, wenn die Bereinigung fehlschlägt oder ein Dateityp nicht unterstützt wird |
| `dropbox_cleansed_archive_path` | nein | `<root>/archive_cleansed` | Verzeichnis für die bereinigten Archive |
| `dropbox_dirty_archive_path` | nein | `<root>/archive_dirty` | Verzeichnis für die Archive der Originale |
| `mail.host` | nein | `localhost` | SMTP-Server; die Verbindung verwendet immer `STARTTLS` |
| `mail.port` | nein | `587` | SMTP-Port |
| `mail.timeout` | nein | `60` | SMTP-Timeout in Sekunden |
| `mail.user`, `mail.password` | nein | | SMTP-Zugangsdaten; ohne `mail.user` wird kein Login versucht |
| `mail.default_sender` | ja | | Absenderadresse der Benachrichtigungs-E-Mails |
| `num_workers` | nein | `1` | Anzahl der Prozesse, die der `worker` für Drops mit Anhängen nutzt |
| `theme_package` | nein | `briefkasten` | Paket, das `templates/editor_email.j2` bereitstellt |
| `testing_secret`, `test_submission_secret` | nein | | aktivieren das Erkennen von Testeinreichungen des [Watchdogs](../deployment/monitoring.md): Ist `testing_secret` vorhanden (der Wert ist egal), wird eine Einreichung, deren Formularfeld `testing_secret` gleich `test_submission_secret` ist, statt an die Redaktion an `watchdog_imap_recipient` geschickt. Im Deployment sind beide auf `post_secret` gesetzt |
| `watchdog_imap_recipient` | mit Watchdog | | Empfänger der Testeinreichungen des Watchdogs |

¹ nur für Drops mit Anhängen nötig.

Das Deployment schreibt außerdem `drop_ttl_days` in die `settings.yaml`. Der `janitor` wertet den Wert aber nicht aus, sondern löscht Drops fest nach 365 Tagen.

## Verzeichnisstruktur des Dropbox-Containers

Fehlende Verzeichnisse werden beim Start angelegt:

```
<fs_dropbox_root>/
├── settings.yaml
├── drops/<drop_id>/     # ein Verzeichnis pro Drop: status, editor_token, message, attach/, clean/, replies/
├── submissions/         # eine leere Datei pro Drop, der auf den Worker wartet
├── scratch/             # Drops, die gerade verarbeitet werden
├── archive_cleansed/    # verschlüsselte Archive der bereinigten Anhänge
├── archive_dirty/       # verschlüsselte Archive der Originalanhänge
└── metrics              # wird von `janitor` geschrieben, unter /metrics ausgeliefert
```

Die Bedeutung der Statuscodes ist unter [Der Lebenszyklus einer Einreichung](workings.md) beschrieben.
