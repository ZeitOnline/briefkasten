import click
import logging
import re
import time
import json
import sys
from imapclient import IMAPClient
from datetime import datetime
from calendar import timegm
from os import environ, path
from pyzabbix import ZabbixMetric, ZabbixSender
from time import sleep
from zope.testbrowser.browser import Browser
from pyquery import PyQuery


import ConfigParser as ConfigParser_

find_drop_id = re.compile('Drop\W(\w+)\s.*')
log = logging.getLogger(__name__)


class ConfigParser(ConfigParser_.SafeConfigParser):
    """ a ConfigParser that can provide its values as simple dictionary.
    taken from http://stackoverflow.com/questions/3220670
    """

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


class WatchdogError(object):

    subject = ''
    message = ''

    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

    def __repr__(self):
        return "[%s] %s" % (self.subject, self.message)


def perform_submission(app_url, testing_secret):
    token = None
    errors = []
    browser = Browser()
    try:
        browser.open(app_url)
    except Exception as exc:
        errors.append(WatchdogError(
            subject="Couldn't open submission page",
            message=u"The attempt to access the submission form resulted in an exception (%s)" % exc))
        return token, errors
    try:
        submit_form = browser.getForm(id='briefkasten-form')
    except LookupError:
        errors.append(WatchdogError(subject=u"Couldn't find submission form",
            message=u"""The contact form was not accessible"""))
        return token
    submit_form.getControl(name='message').value = u'This is an automated test submission from the watchdog instance.'
    submit_form.getControl(name='testing_secret').value = testing_secret
    # TODO: submit attachment
    submit_form.submit()
    response = PyQuery(browser.contents)
    token_element = response("#feedback-token")
    token = None
    if token_element is not None:
        token = token_element.text()
    if not bool(token):
        errors.append(WatchdogError(subject="Couldn't get feedback token",
            message=u"The form submission was successful, but no feedback-token was given at %s" % browser.url))
    return token, errors


def fetch_test_submissions(previous_history, config):
    """ fetch emails from IMAP server using the given configuration
        each email is parsed to see whether it matches a submission
        if so, its token is extracted and checked against the given
        history.
        if found, the email is deleted from the server and the entry
        is removed from the history.
        any entries left in the history are returned
    """
    server = IMAPClient(config['imap_host'], use_uid=True, ssl=True)
    server.login(config['imap_user'], config['imap_passwd'])
    server.select_folder('INBOX')
    history = previous_history.copy()
    candidates = server.fetch(server.search(criteria='NOT DELETED SUBJECT "Drop"'), ['BODY[HEADER.FIELDS (SUBJECT)]'])
    for imap_id, message in candidates.items():
        subject = message.get('BODY[HEADER.FIELDS (SUBJECT)]', 'Subject: ')
        try:
            drop_id = find_drop_id.findall(subject)[0]
        except IndexError:
            # ignore emails that are not test submissions
            continue
        server.delete_messages([imap_id])
        try:
            del history[drop_id]
        except KeyError:
            pass  # TODO: log this?
    server.logout()
    return history


def default_config():
    return dict(
        app_url="http://localhost:6543/briefkasten/",
        max_process_secs=60,
        smtp_host="localhost",
        smtp_port=25,
        log_level='INFO',
        sleep_seconds=0,
    )


def config_from_file(fs_config):
    parser = ConfigParser(allow_no_value=True)
    parser.read(fs_config)
    try:
        return parser.as_dict()['briefkasten']
    except KeyError:
        return dict()


def config_from_env(prefix='BKWD_'):
    keys = [e for e in environ.keys() if e.startswith(prefix)]
    config=dict()
    for key in keys:
        target_key = key.split(prefix)[-1].lower()
        config[target_key] = environ[key]
    return config



@click.command(help='Performs a test submission and checks it arrived')
@click.argument(
    'fs_config',
    required=False,
    default='watchdog.ini',
)
@click.option(
    '--sleep-seconds',
    default=None,
    help='''Run forever and sleep for n seconds between loops''')
def main(fs_config=None, sleep_seconds=None):
    # read configuration
    config = default_config()
    if fs_config is not None:
        fs_config = path.abspath(fs_config)
        config.update(config_from_file(fs_config))
    config.update(config_from_env())

    if sleep_seconds is not None:
        config['sleep_seconds'] = sleep_seconds
    else:
        config['sleep_seconds'] = int(config['sleep_seconds'])

    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, config['log_level'].upper()))

    # read history of previous runs
    errors = []
    fs_history = path.abspath(path.join(path.dirname(fs_config), 'watchdog-history.json'))

    zbx = None
    result_code = None

    if 'zabbix_host' in config:
        zbx = ZabbixSender(config['zabbix_host'])

    while True:
        try:
            if path.exists(fs_history):
                previous_history = json.load(open(fs_history, 'r'))
            else:
                log.info("Starting with empty history.")
                previous_history = dict()

            # fetch submissions from mail server
            log.debug("Fetching previous submissions from IMAP server")
            history = fetch_test_submissions(previous_history=previous_history, config=config)

            # check for failed test submissions
            max_process_secs = int(config['max_process_secs'])
            now = datetime.now()
            for token, timestamp_str in history.items():
                timestamp = datetime.utcfromtimestamp((timegm(time.strptime(timestamp_str.split('.')[0] + 'UTC', "%Y-%m-%dT%H:%M:%S%Z"))))
                age = now - timestamp
                if age.seconds > max_process_secs and token not in previous_history:
                    errors.append(WatchdogError(
                        subject="Submission '%s' not received" % token,
                        message=u"The submission with token %s which was submitted on %s was not received after %d seconds." % (
                            token, timestamp, max_process_secs)))

            # perform test submission
            log.debug("Performing test submissions against {app_url}".format(**config))
            token, submission_errors = perform_submission(
                app_url=config['app_url'],
                testing_secret=config['testing_secret'])
            if token:
                history[token] = datetime.now().isoformat()
            errors += submission_errors

            # record updated history
            file_history = open(fs_history, 'w')
            file_history.write(json.dumps(history).encode('utf-8'))
            file_history.close()

            if len(errors) > 0:
                log.warning("Errors were found.")
                from pyramid_mailer import mailer_factory_from_settings
                from pyramid_mailer.message import Message
                from urlparse import urlparse
                mailer = mailer_factory_from_settings(config, prefix='smtp_')
                hostname = urlparse(config['app_url']).hostname
                recipients = [recipient for recipient in config['notify_email'].split() if recipient]
                message = Message(subject="[Briefkasten %s] Submission failure" % hostname,
                    sender=config['the_sender'],
                    recipients=recipients,
                    body="\n".join([str(error) for error in errors]))
                mailer.send_immediately(message, fail_silently=False)

            result_code = 0

        except Exception as exc:
            log.error(exc)
            result_code = 1

        if zbx is not None:
            log.info("Pinging Zabbix")
            metric = ZabbixMetric(
                config.get('zabbix_sender', 'localhost'),
                'briefkasten.watchdog.last_completed_run', result_code)
            sent = zbx.send([metric])
            if sent.failed > 0:
                log.warning("Failed to ping Zabbix host")

        if config['sleep_seconds'] > 0:
            log.info("Sleeping {sleep_seconds} seconds".format(**config))
            sleep(config['sleep_seconds'])
        else:
            exit(0)
