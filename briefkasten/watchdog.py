import time
import json
from datetime import datetime
from calendar import timegm
from os import path
from zope.testbrowser.browser import Browser
from pyquery import PyQuery


import ConfigParser as ConfigParser_


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


class SubmissionError(object):

    subject = ''
    message = ''

    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

    def __repr__(self):
        return "[%s] %s" % (self.submit_form, self.message)


def perform_submission(app_url=None):
    token = None
    errors = []
    browser = Browser()
    browser.open(app_url)
    try:
        submit_form = browser.getForm(id='briefkasten-form')
    except LookupError:
        errors.append(SubmissionError(subject=u"Couldn't find submission form",
            message=u""""""))
        return token
    submit_form.getControl(name='message').value = u'Hello there'
    # TODO: submit attachment
    submit_form.submit()
    response = PyQuery(browser.contents)
    token_element = response("#feedback-token")
    if token_element is not None:
        token = token_element.text()
    else:
        errors.append(SubmissionError(subject="Couldn't get feedback token",
            message=u"The form submission was successful, but no feedback-token was given at %s" % browser.url))
    return token, errors


def fetch_test_submissions(history=None, config=None):
    """ fetch emails from IMAP server using the given configuration
        each email is parsed to see whether it matches a submission
        if so, its token is extracted and checked against the given
        history.
        if found, the email is deleted from the server and the entry
        is removed from the history.
        any entries left in the history are returned
    """
    return history


def main():
    # read configuration
    fs_config = path.abspath(path.join(path.dirname(__file__), '..', 'watchdog-development.ini'))
    parser = ConfigParser(allow_no_value=True)
    parser.read(fs_config)
    config = parser.as_dict()['briefkasten']

    # read history of previous runs
    errors = []
    fs_history = path.abspath(path.join(path.dirname(__file__), '..',  'var', 'watchdog-history.json'))
    if path.exists(fs_history):
        history = json.load(open(fs_history, 'r'))
    else:
        history = dict()

    # fetch submissions from mail server
    history = fetch_test_submissions(history=history, config=config)

    # check for failed test submissions
    max_process_secs = config.get('max_process_secs', 600)
    now = datetime.now()
    for token, timestamp_str in history.items():
        timestamp = datetime.utcfromtimestamp((timegm(time.strptime(timestamp_str.split('.')[0] + 'UTC', "%Y-%m-%dT%H:%M:%S%Z"))))
        age = now - timestamp
        if age.seconds > max_process_secs:
            errors.append(SubmissionError(subject="Submission '%s' not received" % token,
                message=u"The submission with token %s which was submitted on %s was not received after %d seconds." % (token, timestamp, max_process_secs)))

    # perform test submission
    token, errors = perform_submission(app_url=config['app_url'])
    history[token] = datetime.now().isoformat()

    # record result of test submission
    file_history = open(fs_history, 'w')
    file_history.write(json.dumps(history).encode('utf-8'))
    file_history.close()
    for error in errors:
        print error


def send_notification(subject=u'', message=u''):
    pass
