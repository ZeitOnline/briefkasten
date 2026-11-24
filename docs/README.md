# Briefkasten

Der `briefkasten` ist eine – soweit sinnvoll möglich – sichere Webanwendung, über die Inhalte anonym an die Redaktion übermittelt werden können.

Hochgeladene Anhänge werden in einer abgeschotteten Umgebung von Metadaten bereinigt, die die Identität der einreichenden Person verraten könnten. Anschließend werden Nachricht und bereinigte Anhänge mit PGP verschlüsselt und per E-Mail an eine festgelegte Liste von Redaktionsmitgliedern geschickt. Die Originaldateien werden danach vom Server gelöscht. Damit sollen weder Admins mit Zugriff auf den Server an die Einreichungen gelangen, noch soll die Redaktion Zugriff auf das unbereinigte Rohmaterial haben.

Nach dem Absenden erhält die einreichende Person eine eindeutige URL, unter der sie den Status ihrer Einreichung und Antworten der Redaktion abrufen kann. Auf dem Server bleiben danach nur der Status, ein Zugangstoken für die Redaktion und deren Antworten – sowie, falls so konfiguriert, verschlüsselte Archive der Anhänge. Was genau wann gespeichert und gelöscht wird, beschreibt [Der Lebenszyklus einer Einreichung](application/workings.md).

Das Projekt enthält nicht nur die Anwendung selbst, sondern auch ein vollständiges Deployment-Setup für FreeBSD-Jails, so dass jede\*r mit überschaubarem Aufwand einen eigenen `briefkasten` betreiben kann.

## Aufbau des Repositorys

| Verzeichnis | Inhalt |
|---|---|
| `application/` | die Webanwendung (Pyramid) samt Worker, Bereinigungsskripten und Themes |
| `deployment/` | Installation und Konfiguration eines FreeBSD-Hosts mit ploy, Ansible und Fabric |
| `watchdog/` | End-to-End-Überwachung einer laufenden Instanz |
| `docs/` | diese Dokumentation |

## Dokumentation

[Deployment](deployment/index.md)

> Installation, Konfiguration und Betrieb einer eigenen Instanz; dazu das [Monitoring](deployment/monitoring.md).

[Anwendung](application/develop.md)

> Lokale Entwicklung, Tests und eigene Themes; dazu die [Konfiguration](application/configuration.md), [Der Lebenszyklus einer Einreichung](application/workings.md) und die [Internationalisierung](application/i18n.md).
