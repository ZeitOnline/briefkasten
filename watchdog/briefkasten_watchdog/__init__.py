import re
import time
import json
from imapclient import IMAPClient
from datetime import datetime
from calendar import timegm
from os import path
from zope.testbrowser.browser import Browser
from pyquery import PyQuery


import ConfigParser as ConfigParser_

find_drop_id = re.compile('Drop ID\W(\w+)\s.*')


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
    browser.mech_browser.set_handle_robots(False)
    browser.open(app_url)
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
    candidates = server.fetch(server.search(criteria=['NOT DELETED',
        'SUBJECT "Drop ID"']), ['BODY[HEADER.FIELDS (SUBJECT)]'])
    for imap_id, message in candidates.items():
        subject = message.get('BODY[HEADER.FIELDS (SUBJECT)]', 'Subject: ')
        try:
            drop_id = find_drop_id.findall(subject)[0]
        except IndexError:
            # ignore emails that are not test submissions
            continue
        print "Found submission '%s'" % drop_id
        server.delete_messages([imap_id])
        try:
            del history[drop_id]
        except KeyError:
            pass  # TODO: log this?
    server.logout()
    return history


def main():
    # read configuration
    import sys
    try:
        fs_config = sys.argv[1]
    except IndexError:
        fs_config = path.join(path.dirname(__file__), '..', 'watchdog.ini')
    fs_config = path.abspath(fs_config)
    parser = ConfigParser(allow_no_value=True)
    parser.read(fs_config)
    config = parser.as_dict()['briefkasten']

    # read history of previous runs
    errors = []
    fs_history = path.abspath(path.join(path.dirname(fs_config), 'var', 'watchdog-history.json'))
    if path.exists(fs_history):
        history = json.load(open(fs_history, 'r'))
    else:
        history = dict()

    # fetch submissions from mail server
    history = fetch_test_submissions(previous_history=history, config=config)

    # check for failed test submissions
    max_process_secs = int(config.get('max_process_secs', 600))
    now = datetime.now()
    for token, timestamp_str in history.items():
        timestamp = datetime.utcfromtimestamp((timegm(time.strptime(timestamp_str.split('.')[0] + 'UTC', "%Y-%m-%dT%H:%M:%S%Z"))))
        age = now - timestamp
        if age.seconds > max_process_secs:
            errors.append(WatchdogError(subject="Submission '%s' not received" % token,
                message=u"The submission with token %s which was submitted on %s was not received after %d seconds." % (token, timestamp, max_process_secs)))

    # perform test submission
    token, submission_errors = perform_submission(app_url=config['app_url'],
        testing_secret=config['testing_secret'])
    history[token] = datetime.now().isoformat()
    errors += submission_errors

    # record updated history
    file_history = open(fs_history, 'w')
    file_history.write(json.dumps(history).encode('utf-8'))
    file_history.close()

    if len(errors) == 0:
        exit()

    from pyramid_mailer import mailer_factory_from_settings
    from pyramid_mailer.message import Message
    from urlparse import urlparse
    mailer = mailer_factory_from_settings(config, prefix='smtp_')
    hostname = urlparse(config['app_url']).hostname
    recipients = [recipient for recipient in config['notify_email'].split('\n') if recipient]
    message = Message(subject="[Briefkasten %s] Submission failure" % hostname,
        sender=config['the_sender'],
        recipients=recipients,
        body="\n".join([str(error) for error in errors]))
    mailer.send_immediately(message, fail_silently=False)
