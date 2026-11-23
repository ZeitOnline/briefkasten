# Monitoring

Der Briefkasten ist bewusst so gebaut, dass er möglichst wenig protokolliert – um die Identität der einreichenden Personen auch im Fall eines Einbruchs zu schützen. Damit ist eine nachträgliche Analyse kaum möglich, wenn etwas schiefgeht. Gleichzeitig muss man sich darauf verlassen können, dass das System läuft: Selbst wenn die Webanwendung Einreichungen annimmt und eine Bestätigung anzeigt, könnte jeder andere Teil der Kette (Bereinigen, Verschlüsseln, Versenden) kaputt sein, ohne dass es jemand bemerkt.

Dafür gibt es zwei Bausteine:

- die **Metriken der Anwendung** unter `/metrics`, die vor allem den Zustand der PGP-Schlüssel zeigen, und
- den **Watchdog**, der regelmäßig End-to-End-Tests gegen eine Briefkasten-Instanz fährt.

## Metriken der Anwendung

Der `janitor` läuft per Cronjob täglich in der Worker-Jail. Er

- prüft für jede Adresse in `editors`, ob im Keyring ein Schlüssel vorhanden ist und wann er abläuft (fehlende, nie ablaufende und in weniger als 60 Tagen ablaufende Schlüssel stehen in seiner Ausgabe),
- löscht Drops, deren Status sich seit mehr als 365 Tagen nicht geändert hat (Drops des Watchdogs nach einem Tag), und
- schreibt die Datei `metrics` in den Dropbox-Container.

Die Webanwendung liefert diese Datei unter `/metrics` aus; nginx leitet den Pfad an den Appserver weiter. Sie enthält eine Metrik pro Schlüssel:

```
pgp_key_expiry_unixtime{user="editor@example.com"} 1767225600.000
```

## Watchdog

Der Watchdog liegt im Verzeichnis `watchdog/` des Repositorys (Paket `briefkasten_watchdog`, Python ≥ 3.14). Er läuft getrennt vom Briefkasten – idealerweise in einem anderen Netz, denn von dort kommen auch die Nutzer\*innen. Wo und wie er betrieben wird, ist nicht Teil dieses Repositorys.

### Ablauf

1. `watchdog submit` öffnet das Formular der Instanz, schickt eine Testnachricht mit dem Feld `testing_secret` ab, liest die Drop-ID von der Rückmeldeseite und merkt sie sich mit Zeitstempel in einer lokalen dbm-Datenbank.
2. Der Briefkasten erkennt die Testeinreichung am Secret und schickt die verschlüsselte E-Mail (Betreff `Drop <drop_id>`) nicht an die Redaktion, sondern an `watchdog_imap_recipient`.
3. Eingehende E-Mails an diese Adresse werden über die [Parse API von Mailjet](https://dev.mailjet.com/email/guides/parse-api/) als Webhook an `watchdog receive` weitergereicht. Der Watchdog streicht die Drop-ID aus seiner Liste und protokolliert, wie lange die Zustellung gedauert hat. Drop-IDs, die nach `--max-process-secs` noch nicht angekommen sind, meldet er als Warnung.
4. Nach jedem Schritt schiebt er seine Metriken an ein Prometheus-Pushgateway.

### Kommandos

| Kommando | Zweck | Optionen (Standard) |
|---|---|---|
| `watchdog submit` | eine Testeinreichung abschicken | `--app-url` (`http://localhost:6543/briefkasten/`), `--testing-secret`, `--dbm-path` (`drops`) |
| `watchdog receive` | HTTP-Server auf Port 8000 für den Mailjet-Webhook | `--dbm-path`, `--pattern` (`^Drop (?P<token>[0-9A-z]+)$`), `--max-process-secs` (`300`) |
| `watchdog dump` | offene Testeinreichungen auflisten | `--dbm-path` |
| `watchdog prune` | alte offene Testeinreichungen löschen | `--dbm-path`, `--days` (`7`) |

Alle Optionen lassen sich auch über Umgebungsvariablen mit dem Präfix `BKWD_` setzen, z. B. `BKWD_APP_URL` oder `BKWD_TESTING_SECRET`. Außerdem werden gelesen:

- `BKWD_PROMETHEUS_PUSH_GATEWAY_URL` – URL des Pushgateways
- `BKWD_ENVIRONMENT` – wird Teil des Job-Namens `briefkasten_watchdog_<environment>`
- `BKWD_LOG_LEVEL` – Log-Level (Standard `info`)

Lokal ausprobieren:

```
$ cd watchdog
$ uv sync
$ uv run watchdog submit --app-url https://<fqdn>/briefkasten/ --testing-secret <post_secret>
```

### Metriken des Watchdogs

| Metrik | Bedeutung |
|---|---|
| `briefkasten_watchdog_last_success_unixtime` | Zeitpunkt, zu dem zuletzt eine Testeinreichung angekommen ist |
| `briefkasten_watchdog_last_test_submission_unixtime` | Zeitpunkt der letzten Testeinreichung |
| `briefkasten_watchdog_pending_test_submission_count` | Anzahl der Testeinreichungen, die noch nicht angekommen sind |

### Konfiguration auf Seiten des Briefkastens

- Das Secret für Testeinreichungen ist im Deployment dasselbe wie `post_secret`: Die Rollen schreiben `post_secret` sowohl als `testing_secret` als auch als `test_submission_secret` in die `settings.yaml`. Der Watchdog muss deshalb mit `--testing-secret <post_secret>` laufen. (Der Schlüssel `test_submission_secret` in den Vorlagen `plain.conf` und `vbox.conf` wird nicht verwendet.)
- `watchdog_imap_recipient` in `ploy.conf` legt fest, wohin die E-Mails der Testeinreichungen gehen.

Siehe auch [Konfiguration](../application/configuration.md#drop-verarbeitung-settingsyaml).
