import click
import configparser
import logging
import sys
from click import group, option
from datetime import datetime
from dbm import open as dbm_open
from http.server import HTTPServer, BaseHTTPRequestHandler
from json import loads, dumps
from os import environ, path
from re import search
from time import time
from zope.testbrowser.browser import Browser
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from pyquery import PyQuery

log = logging.getLogger(__name__)

REGISTRY = CollectorRegistry()

last_success = Gauge(
    'job_last_briefkasten_watchdog_success_unixtime',
    'Last time a briefkasten watchdog job successfully finished',
    registry=REGISTRY)


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


def perform_submission(app_url, testing_secret):
    browser = Browser()
    try:
        browser.open(app_url)
    except Exception as exc:
        log.error("[Couldn't open submission page] The attempt to access the "
                  "submission form resulted in an exception (%s)", exc)
        return None
    try:
        submit_form = browser.getForm(id="briefkasten-form")
    except LookupError:
        log.error("[Couldn't find submission form] The contact form was not accessible")
        return None
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
        log.error("[Couldn't get feedback token] The form submission was successful, "
                  "but no feedback-token was given at %s", browser.url)
    return token


def receive_test_submissions(handler):
    """ Receive test mails via MailJet's "Parse API" webhook (ee
        https://dev.mailjet.com/email/guides/parse-api/) and calls
        the given handle function. """
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            log.info('do_POST')
            content_length = self.headers['Content-Length']
            data = self.rfile.read(int(content_length))
            payload = loads(data)
            log.info('Received mail from {From}: "{Subject}"'.format(**payload))
            log.info(dumps(payload, sort_keys=True, indent=2))
            handler(payload)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Thank you')

    with HTTPServer(('', 8000), Handler) as httpd:
        log.info('receiver ready')
        httpd.serve_forever()


def push_to_prometheus(config):
    push_to_gateway(
        config['prometheus_push_gateway_url'],
        job="briefkasten_watchdog_{environment}".format(**config),
        registry=REGISTRY)


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


@group()
def cli():
    pass


@cli.command(context_settings=dict(auto_envvar_prefix='BKWD_'))
@option('--app-url', default='http://localhost:6543/briefkasten/', help='application URL')
@option('--testing-secret', default='', help='secret used to distinguish test submissions')
@option('--dbm-path', default='drops', help='path to dbm database for storing drops')
def submit(app_url, testing_secret, dbm_path):
    """ Perform test submission """
    log.debug("Performing test submissions against %s", app_url)
    token = perform_submission(app_url, testing_secret)
    with dbm_open(dbm_path, 'c') as db:
        db[token] = str(time())
    log.info("Created drop with token %s", token)


@cli.command(context_settings=dict(auto_envvar_prefix='BKWD_'))
@option('--dbm-path', default='drops', help='path to dbm database for storing drops')
@option('--pattern', default=r'^Drop (?P<token>[0-9A-z]+)$', help='pattern mail subjects must match')
@option('--max-process-secs', default=300, help='time allowed for test submission to arrive')
def receive(dbm_path, pattern, max_process_secs):
    """ Receive test submissions """
    def handler(payload):
        match = search(pattern, payload.get('Subject', ''))
        if match is not None:
            now = time()
            token = match.group('token')
            with dbm_open(dbm_path, 'c') as db:
                if token in db:
                    elapsed = now - float(db[token])
                    log.info(f'Received token {token} after {elapsed:.1f} seconds')
                    last_success.set_to_current_time()
                    del db[token]
                else:
                    log.warning(f'Received unknown token "{token}"')
                for token in db.keys():
                    sent = float(db[token])
                    if now - sent > max_process_secs:
                        log.warning("[Slow test submission] The submission with token '%s' "
                                    "which was submitted on %s was not received after %d seconds.",
                                    token.decode(), datetime.fromtimestamp(sent), max_process_secs)
    # start http server passing the handler
    receive_test_submissions(handler)


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
    cli()
