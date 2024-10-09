# The life cycle of a submission

Users entrusting us with sensitive data is the key concern of the software and when and getting it straight where this data is stored for how long in what form is crucial.

The stages are numbered with a three digit integer code, allowing to group and sort them.

Status codes beginning with `0` mean that the submission is still being handled by the web application (and implies that it is still unencrypted)

The life of a submission begins with the POST of the client browser succeeding.
Any attachments are first stored in memory before writing them to disk into a dedicated dropbox directory.
At this point the submission has the status `010 received` and is readable in plaintext by any attacker who gains access to the application jail.

Next, the web application hands off the submission to an external processing script, which immediately either errors out or acknowledges the receipt of the drop directory.

The error case at this stage means that the cleansing setup is seriously broken and the web application will take it upon itself to delete the attachments immediately to avoid exposing them in plaintext unduly.
(TODO: a cronjob on the jailhost should additionally monitor for dropboxes in the 'submitted' or 'submitted failed' state for longer than a given threshold)

If the submission was successful (the process script returns `0` as exit code) the dropbox is considered to be `020 submitted`.

Once submitted, the cleanser performs basic sanity checking. If that fails for whatever reason it will set the status to `500 cleanser init failure`. Since it's basically being able to accept the attachments it will delete the attachment itself (TODO: confirm with @erdgeist)

If the process script determines that the cleansing setup is intact (whether locally or via one or more cleanser jails) it will set the status to `100 processing`.
The submission still resides in plaintext inside the application jail.

The process will now initiate the cleansing, either locally or by submitting it to a cleanser jail. Either way, once the submission is sucessful, the status will change to `200 quarantined`, and the submission is (finally) no longer readable inside the application jail.

If submission has failed the status will be set to `501 cleanser submission failure` and the attachments will be deleted.

Now we are left with three possible outcomes: success, failure during cleansing or timeout:

- `510 cleanser processing failure`
- `520 cleanser timeout failure`
- `900 success`

In all cases except `900` the attachments will have been deleted from the fileystem of the briefkasten host.
