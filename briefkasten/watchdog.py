import json
from datetime import datetime
from os import path
from ConfigParser import SafeConfigParser
from zope.testbrowser.browser import Browser
from pyquery import PyQuery


class SubmissionError(object):

    subject = ''
    message = ''

    def __init__(self, subject, message):
        self.subject = subject
        self.message = message


def perform_submission(app_url):
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


def main():
    fs_config = path.abspath(path.join(path.dirname(__file__), '..', 'watchdog-development.ini'))
    parser = SafeConfigParser(allow_no_value=True)
    parser.read(fs_config)
    errors = []
    fs_history = path.abspath(path.join(path.dirname(__file__), '..',  'var', 'watchdog-history.json'))
    if path.exists(fs_history):
        history = json.load(open(fs_history, 'r'))
    else:
        history = dict()
    token, errors = perform_submission(parser.get('briefkasten', 'app_url'))
    history[token] = datetime.now().isoformat()
    file_history = open(fs_history, 'w')
    file_history.write(json.dumps(history).encode('utf-8'))
    file_history.close()


def send_notification(subject=u'', message=u''):
    pass
