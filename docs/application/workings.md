# Der Lebenszyklus einer Einreichung

Dass Menschen uns sensible Daten anvertrauen, ist das zentrale Anliegen dieser Software. Entscheidend ist daher, genau festzuhalten, wo diese Daten wie lange in welcher Form gespeichert werden.

Jeder Drop hat einen Status, der in `drops/<drop_id>/status` im Dropbox-Container steht. Er beginnt mit einem dreistelligen Code, so dass sich die Stufen gruppieren und sortieren lassen. Die Rückmeldeseite und die Redaktionsseite zeigen diesen Status an.

## In der Webanwendung

Das Leben einer Einreichung beginnt, wenn der Browser das Formular lädt. Es enthält ein signiertes Token mit einer neuen Drop-ID, das nur eine begrenzte Zeit gültig ist (`post_token_max_age_seconds`).

Lädt der Browser (per JavaScript) Anhänge hoch oder schickt er das Formular ab, legt die Webanwendung das Verzeichnis `drops/<drop_id>/` an (Status `010 created`) und schreibt die Nachricht nach `message`, die Anhänge nach `attach/` und ein zufälliges Editor-Token nach `editor_token`.
**Ab hier liegt die Einreichung im Klartext auf der Festplatte** – im Deployment im gemeinsamen Dataset von Appserver- und Worker-Jail.

Mit dem Absenden legt die Webanwendung eine leere Datei `submissions/<drop_id>` an und setzt den Status auf `020 submitted`. Danach leitet sie auf die Rückmeldeseite `dropbox/<drop_id>` weiter. Ein Drop im Status `020` oder höher nimmt keine weiteren Daten mehr an.

## Im Worker

Der `worker` bemerkt die neue Datei in `submissions/` und verarbeitet den Drop. Drops ohne Anhänge werden direkt verarbeitet, Drops mit Anhängen in einem Pool aus `num_workers` Prozessen.

Hat der Drop Anhänge:

1. `100 processor running`, dann `101 creating initial encrypted backup`: Die Originalanhänge werden zusammen mit der Nachricht in ein ZIP gepackt und für alle Redaktionsmitglieder mit gültigem Schlüssel verschlüsselt (`dirty.zip.pgp`). Hat niemand einen gültigen Schlüssel, kann nichts verschlüsselt werden; der Drop endet dann mit `500 no valid keys at all` oder `605 smtp failure`.
2. `105 processing attachments`: `process-attachments.sh` aus `fs_bin_path` wird aufgerufen. Im Deployment holt sich das Skript über `jdispatch` eine freie Cleanser-Jail (`201`), kopiert das Drop-Verzeichnis per `scp` dorthin (`203`) und lässt die Anhänge dort bereinigen (`204`): Word-Dokumente werden zu PDF, PDFs und Bilder werden neu erzeugt, Textdateien werden kopiert. Danach wird das Ergebnis nach `clean/` zurückkopiert und die Cleanser-Jail auf einen sauberen Snapshot zurückgesetzt.
3. Das Skript hinterlässt einen der folgenden Zustände:
    - einen Code unter `500` – die Bereinigung war erfolgreich,
    - `800 Not cleansible` – mindestens ein Dateityp ist unbekannt und wurde unverändert kopiert,
    - `5xx` – die Bereinigung ist fehlgeschlagen, z. B. `502 No remote cleanser available`, `504`/`505` beim Kopieren, `520 cleanser timeout failure` oder `540 Error while cleasing file of type …`.
4. Sind die bereinigten Anhänge größer als `attachment_size_threshold`, werden sie nicht per E-Mail verschickt, sondern verschlüsselt in `archive_cleansed/` abgelegt (`270 creating final encrypted backup of cleansed attachments`).
5. Ist `dropbox_dirty_archive_url_format` konfiguriert, wird bei `5xx` und `800` das verschlüsselte Backup der Originale nach `archive_dirty/` verschoben; bei `5xx` wird der Status dann auf `490 cleanser failure but notify success` gesetzt.

Anschließend wird die Redaktion benachrichtigt, sofern der Status unter `500` liegt oder `800` ist: Jedes Redaktionsmitglied mit gültigem Schlüssel bekommt eine eigene, mit seinem Schlüssel verschlüsselte E-Mail mit der Nachricht, den Links zur Redaktionsseite und zu den Archiven sowie gegebenenfalls den bereinigten Anhängen. Das Ergebnis:

- `900 success` – die E-Mails wurden verschickt,
- `605 smtp failure` – es konnte keine einzige E-Mail erstellt werden (kein Redaktionsmitglied mit gültigem Schlüssel),
- `610 smtp error (…)` – der Versand ist fehlgeschlagen.

Bei einem Fehler in der Bereinigung ohne konfiguriertes Archiv der Originale wird die Redaktion nicht benachrichtigt.

## Was danach übrig bleibt

Unabhängig vom Ergebnis löscht der Worker am Ende `message`, `dirty.zip.pgp`, `attach/` und `clean/`. Im Drop-Verzeichnis bleiben nur:

- `status`,
- `editor_token`,
- Antworten der Redaktion in `replies/`, die die einreichende Person auf der Rückmeldeseite lesen kann.

Dazu kommen, falls konfiguriert, die verschlüsselten Archive in `archive_cleansed/` und `archive_dirty/`. Sie werden vom Briefkasten nicht automatisch gelöscht.

Der `janitor` löscht Drop-Verzeichnisse, deren Status sich seit mehr als 365 Tagen nicht geändert hat; Drops des [Watchdogs](../deployment/monitoring.md) schon nach einem Tag.

## Übersicht der Statuscodes

| Code | Gesetzt von | Bedeutung |
|---|---|---|
| `010 created` | Webanwendung | Drop-Verzeichnis angelegt |
| `020 submitted` | Webanwendung | Formular abgeschickt, wartet auf den Worker |
| `100 processor running` | Worker | Verarbeitung eines Drops mit Anhängen begonnen |
| `101 creating initial encrypted backup` | Worker | Originalanhänge werden verschlüsselt gesichert |
| `105 processing attachments` | Worker | `process-attachments.sh` läuft |
| `201`–`204` | `process-attachments.sh` | Cleanser-Jail zugeteilt, Daten kopiert, Bereinigung läuft |
| `270 creating final encrypted backup of cleansed attachments` | Worker | bereinigte Anhänge werden archiviert statt verschickt |
| `490 cleanser failure but notify success` | Worker | Bereinigung fehlgeschlagen, Originale archiviert, Redaktion wird benachrichtigt |
| `500 no valid keys at all` | Worker | kein Redaktionsmitglied hat einen gültigen Schlüssel |
| `501`–`505`, `520`, `540` | `process-attachments.sh` | Bereinigung fehlgeschlagen |
| `605 smtp failure` | Worker | keine E-Mail erstellt |
| `610 smtp error (…)` | Worker | Versand fehlgeschlagen, mit Traceback |
| `800 Not cleansible` | `process-attachments.sh` | mindestens ein Anhang konnte nicht bereinigt werden; wird trotzdem verschickt |
| `900 success` | Worker | Redaktion benachrichtigt |

Lokal und in den Tests ersetzt ein Mock-Skript die Bereinigung; es meldet `299 Cleansed` (oder auf Wunsch `540`/`800`).
