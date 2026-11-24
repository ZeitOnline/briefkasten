# The life cycle of a submission

Submitters entrusting the operators of a `briefkasten` with sensitive data is the key concern of the software, and getting it straight where this data is stored, for how long and in what form is crucial.

Each stage of a submission is recorded in a status file inside its drop directory. The stages are numbered with a three digit integer code, allowing to group and sort them:

- `0xx` – the submission is still being handled by the web application (which implies that it is still unencrypted)
- `1xx` – `4xx` – the submission is being processed
- `5xx` – processing has failed
- `6xx` – sending the submission to the editors has failed
- `800` – at least one attachment could not be cleansed
- `900` – success

## Receiving the submission

The life of a submission begins with the POST of the client browser succeeding.
Any attachments are first stored in memory before writing them to disk into a dedicated drop directory.
At this point the submission has the status `010 created` and is readable in plaintext by any attacker who gains access to the application jail.

Next, the web application puts the submission into the submission queue, which sets the status to `020 submitted`.

## Processing

The `worker` process watches the submission queue and picks up new submissions. Submissions without attachments are sent to the editors right away.

For submissions with attachments the status changes to `100 processor running`. The worker first creates an encrypted backup of the original attachments (`101 creating initial encrypted backup`) and then hands them to the sanitizing scripts (`105 processing attachments`). The actual cleansing happens in one of the separate cleanser jails, which is reflected by the following statuses:

- `201`/`202` – a cleanser jail has been acquired and the data is being copied to it
- `203` – the attachments are being processed by the cleanser
- `204` – the attachments are in quarantine on the cleanser

If the cleansed attachments exceed the configured size threshold, an encrypted archive of them is created outside of the drop directory (`270 creating final encrypted backup of cleansed attachments`) and the editors will receive a link to it instead of the attachments themselves.

## Failures

If anything goes wrong during processing, the status will be set to one of the following codes:

- `500 no valid keys at all` – none of the editors has a valid PGP key
- `501` – `505` – the cleansing setup is broken (i.e. the drop directory isn't accessible, no cleanser is available or copying the data from or to the cleanser failed)
- `520 cleanser timeout failure`
- `540` – an attachment could not be cleansed due to an error
- `800 Not cleansible` – at least one attachment has a file type that isn't supported

Optionally, the original (uncleansed) attachments of failed submissions can be archived in encrypted form, see `dropbox_dirty_archive_url_format` in the deployment configuration. In this case the status will be set to `490 cleanser failure but notify success` and the editors will be notified.

## Notifying the editors

Finally, the (cleansed) submission is encrypted for and sent to each of the editors via email. If this succeeds, the status will be set to `900 success`, otherwise to `605 smtp failure` or `610 smtp error`.

## Cleaning up

In all cases the message and the attachments will be deleted from the drop directory once processing is complete. The only data kept on the server is the status file and any replies the editors may post for the submitter. Drop directories that haven't changed for a year (or for a day in the case of test submissions by the watchdog) are removed entirely by the `janitor`, which additionally checks the editors' PGP keys for upcoming expiry.
