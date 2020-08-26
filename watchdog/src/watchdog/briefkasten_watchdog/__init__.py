import click
import logging
import re
import sys
from imapclient import IMAPClient
from datetime import datetime
from os import environ, path
from time import sleep
from zope.testbrowser.browser import Browser
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from pyquery import PyQuery

import configparser as configparser

find_drop_id = re.compile("Drop\W(\w+)\s.*")
log = logging.getLogger(__name__)


class ConfigParser(configparser.ConfigParser):
    """ a ConfigParser that can provide its values as simple dictionary.
    taken from http://stackoverflow.com/questions/3220670
    """

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop("__name__", None)
        return d


class WatchdogError(object):

    subject = ""
    message = ""

    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

    def __repr__(self):
        return "[%s] %s" % (self.subject, self.message)


def perform_submission(app_url, testing_secret):
    token = None
    errors = []
    now = datetime.now()
    browser = Browser()
    try:
        browser.open(app_url)
    except Exception as exc:
        errors.append(
            WatchdogError(
                subject="Couldn't open submission page",
                message=u"The attempt to access the submission form resulted in an exception (%s)"
                % exc,
            )
        )
        return token, now, errors
    try:
        submit_form = browser.getForm(id="briefkasten-form")
    except LookupError:
        errors.append(
            WatchdogError(
                subject=u"Couldn't find submission form",
                message=u"""The contact form was not accessible""",
            )
        )
        return token, now, errors
    submit_form.getControl(
        name="message"
    ).value = u"This is an automated test submission from the watchdog instance."
    submit_form.getControl(name="testing_secret").value = testing_secret
    # TODO: submit attachment
    submit_form.submit()
    response = PyQuery(browser.contents)
    token_element = response("#feedback-token")
    token = None
    if token_element is not None:
        token = token_element.text()
    if not bool(token):
        errors.append(
            WatchdogError(
                subject="Couldn't get feedback token",
                message=u"The form submission was successful, but no feedback-token was given at %s"
                % browser.url,
            )
        )
    return token, now, errors


def fetch_test_submissions(config, target_token):
    """ fetch emails from IMAP server using the given configuration
        each email is parsed to see whether it matches a submission
        if so, its token is extracted and checked against the given
        one.
        if found, the email is deleted from the server and True is returned
    """
    from distutils import util
    use_ssl = bool(util.strtobool(config.get('imap_ssl', True)))
    server = IMAPClient(
        config["imap_host"], port=int(config.get("imap_port", 143)), use_uid=True, ssl=use_ssl,
    )
    server.login(config["imap_user"], config["imap_passwd"])
    server.select_folder("INBOX")
    candidates = server.fetch(
        server.search(criteria='NOT DELETED SUBJECT "Drop"'),
        ["BODY[HEADER.FIELDS (SUBJECT)]"],
    )
    success = False
    for imap_id, message in candidates.items():
        subject = message.get(b"BODY[HEADER.FIELDS (SUBJECT)]", "Subject: ")
        try:
            drop_id = find_drop_id.findall(subject.decode('utf-8'))[0]
        except IndexError:
            # ignore emails that are not test submissions
            continue
        if drop_id == target_token:
            server.delete_messages([imap_id])
            success = True
            log.info("Success! Found %s" % target_token)
            break
    server.logout()
    return success


def send_error_email(errors, config):
    if len(errors) == 0:
        return
    log.warning("Errors were found.")
    from pyramid_mailer import mailer_factory_from_settings
    from pyramid_mailer.message import Message
    from urllib.parse import urlparse

    mailer = mailer_factory_from_settings(config, prefix="smtp_")
    hostname = urlparse(config["app_url"]).hostname
    recipients = [
        recipient
        for recipient in config["notify_email"].split()
        if recipient
    ]
    body = "\n".join([str(error) for error in errors])
    message = Message(
        subject="[Briefkasten %s] Submission failure" % hostname,
        sender=config["the_sender"],
        recipients=recipients,
        body=body,
    )
    mailer.send_immediately(message, fail_silently=False)


def push_to_prometheus(errors, config):
    if len(errors) > 0:
        return
    log.info("No Errors were found, pushing success to prometheus/")
    registry = CollectorRegistry()
    gauge = Gauge(
        'job_last_briefkasten_watchdog_success_unixtime',
        'Last time a briefkasten watchdog job successfully finished',
        registry=registry)
    gauge.set_to_current_time()
    push_to_gateway(
        config['prometheus_push_gateway_url'],
        job="briefkasten_watchdog_{environment}".format(**config),
        registry=registry)


def default_config():
    return dict(
        app_url="http://localhost:6543/briefkasten/",
        max_process_secs=60,
        smtp_host="localhost",
        smtp_port=25,
        log_level="INFO",
        sleep_seconds=0,
        retry_seconds=20,
        max_attempts=3,
    )


def config_from_file(fs_config):
    parser = ConfigParser(allow_no_value=True)
    parser.read(fs_config)
    try:
        return parser.as_dict()["briefkasten"]
    except KeyError:
        return dict()


def config_from_env(prefix="BKWD_"):
    keys = [e for e in environ.keys() if e.startswith(prefix)]
    config = dict()
    for key in keys:
        target_key = key.split(prefix)[-1].lower()
        config[target_key] = environ[key]
    return config


def once(config):
    # perform test submission
    log.debug("Performing test submissions against {app_url}".format(**config))
    token, timestamp, errors = perform_submission(
        app_url=config["app_url"], testing_secret=config["testing_secret"]
    )
    log.info("Created drop with token %s" % token)
    # fetch submissions from mail server
    if token is not None:
        log.debug("Fetching previous submissions from IMAP server")
        attempts = 0
        while True:
            log.info("Waiting {retry_seconds} seconds".format(**config))
            sleep(int(config["retry_seconds"]))
            success = fetch_test_submissions(config, token)
            attempts += 1
            if success or attempts >= int(config['max_attempts']):
                break
            log.info("Retrying fetching %s" % token)

        # check for failed test submissions
        now = datetime.now()
        age = now - timestamp
        max_process_secs = int(config['max_process_secs'])
        if success and age.seconds > max_process_secs:
            errors.append(
                WatchdogError(
                    subject="Submission '%s' not received in time" % token,
                    message=u"The submission with token %s submitted on %s was received, but it took %d seconds instead of %d."
                    % (token, timestamp, age.seconds, max_process_secs),
                )
            )
        if not success:
            errors.append(
                WatchdogError(
                    subject="Submission '%s' not received" % token,
                    message=u"The submission with token %s which was submitted on %s was not received after %d seconds."
                    % (token, timestamp, max_process_secs),
                )
            )
    send_error_email(errors, config)
    push_to_prometheus(errors, config)
    if errors:
        log.error(errors)
    return errors


@click.command(help="Performs a test submission and checks it arrived")
@click.argument(
    "fs_config", required=False, default="watchdog.ini",
)
def main(fs_config=None):
    config = default_config()
    if fs_config is not None:
        fs_config = path.abspath(fs_config)
        config.update(config_from_file(fs_config))
    config.update(config_from_env())
    logging.basicConfig(
        stream=sys.stdout, level=getattr(logging, config["log_level"].upper())
    )

    once(config)


if __name__ == '__main__':
    main()
