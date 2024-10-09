# Monitoring

Since the whole system is configured by design not to log anything in order to protect the identity of submitters in case of a break-in, it is pretty much impossible to perform any post-mortem anyalysis when something has gone wrong. At the same time it is vital that you can be sure that the system is up and running at all times. Even if the web application is running and submitters can post data (and even receive a token as confirmation) any other part of the chain (sanitizing, encrypting and sending of the submitted material) could be broken without anybody noticing it. To this end, we've included a dedicated **watchdog** application which performs regular **end to end** tests of a `briefkasten` instance.

Ideally, the watchdog is installed on another machine, preferably on another network (afterall, that's where your users will be coming from, too).

To install it, use a checkout of this project but use the `watchdog.cfg` configuration for running buildout, like so:

```
$ bootstrap -c watchdog.cfg
$ bin/buildout -c watchdog.cfg

..TODO: provide a ``make watchdog`` target.
```

This will install an executable in `bin/watchdog` which is designed to be called without parameters, i.e. from a `crontab` entry.

It expects its configuration in `etc/watchdog.ini` with the following values:

```
app_url = # full URL to the submit form, i.e. ``https://ssl.zeit.de/briefkasten/submit``
test_token = # a unique string that will trigger the test submission when the watchdog submits a POST
max_process_secs = # time in seconds which it allows a submission to take to complete before it deems it failed.
imap_recipient = # email address to which the test submission should be sent to
imap_host =
imap_user =
imap_passwd =
notify_email = one or more (one per line) email recipients that should receive notification if something went wrong.
# smtp settings for pyramid_mailer, see
# http://docs.pylonsproject.org/projects/pyramid_mailer/en/latest/
smtp_host = localhost
smtp_port = 25
smtp_username = blubber
smtp_password = fooberific
smtp_tls = true
```

When run, the script will:

> - log into the IMAP account and retrieve any new emails that look like a `briefkasten` submission, noting their token in a timestamped list of actually received notifications.
> - it then compares this list with the ones it expects a submission for. any tokens found are removed.
> - any tokens remaining with a time stamp older than the maximum allowed processing time trigger a notification email.
> - next, it performs a test submission at the given url. It sends the preconfigured token using a `X-Briefkasten-Testing-Token` header in the request.
> - it then parses the response and stores the token received in the list for which it expects a submission.
> - If anything went wrong during that process it sends out the notification(s) and terminates.

Note, that unlike the application itself, the watchdog does keep detailed logs of all the steps described above, allowing some minimal post-mortem analysis without compromising actual 'real world' submissions.
