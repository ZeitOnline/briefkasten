# -*- coding: utf-8 -*-
from os import listdir
from os.path import join, dirname
from pytest import fixture
from webtest import Upload


def test_visit_fingerprint(browser):
    response = browser.get('/briefkasten/fingerprint')
    response.status == '200 OK'


def test_successful_submission(browser):
    response = browser.post('/briefkasten/submit', params=dict(message=u'hey'))
    assert response.status == '302 Found'
    redirected = browser.get(response.location)
    assert u'No reply has been posted so far' in redirected.text


def test_submission_validation_failure(browser):
    response = browser.post('/briefkasten/submit', params=dict(message=u''))
    assert response.status == '200 OK'
    assert u'Es gab ein Problem mit Ihren Angaben' in response.text


@fixture
def form(browser):
    from briefkasten import views
    # patch the default number of attachments, since the browser cannot execute javascript
    views.attachments_min_len = 3
    return browser.get('/briefkasten/submit').forms[0]


def test_submission_with_one_attachment_post(form):
    from briefkasten import dropbox_container
    assert len(listdir(dropbox_container.fs_path)) == 0
    from briefkasten.views import tempstore
    assert len(tempstore.keys()) == 0
    form.set('upload', Upload('attachment.txt', open(join(dirname(__file__), 'attachment.txt'), 'r').read(), 'text/plain'), index=0)
    form['message'] = 'Hello there'
    form.submit()
    # ensure that the temporary storage has been cleared
    assert len(tempstore.keys()) == 0
    fs_dropbox = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0])
    assert len(listdir(join(fs_dropbox, 'attach'))) == 1
    fs_attachments = join(dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'attach')
    fs_attachment = join(fs_attachments, listdir(fs_attachments)[0])
    assert open(fs_attachment).read().decode('utf-8') == \
        open(join(dirname(__file__), 'attachment.txt'), 'r').read().decode('utf-8')


def test_submission_with_multiple_attachments(form):
    from briefkasten import dropbox_container
    form.set('upload', Upload('attachment.txt', open(join(dirname(__file__), 'attachment.txt'), 'r').read(), 'text/plain'), index=0)
    # we skip the second upload field simply to cover that edge case while we're at it...
    form.set('upload', Upload('attachment.png', open(join(dirname(__file__), 'attachment.png'), 'r').read(), 'image/png'), index=2)
    form['message'] = 'Hello there'
    form.submit()
    fs_attachments = join(dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'attach')
    assert len(listdir(fs_attachments)) == 2


def test_submission_generates_message_to_editors(browser):
    browser.post('/briefkasten/submit', params=dict(message=u'Hello'))
    from briefkasten import dropbox_container
    fs_message = join(dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'message')
    created_message = open(fs_message).read().decode('utf-8')
    assert u'Hello' in created_message
    editor_token = open(join(dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'editor_token')).read().decode('utf-8')
    assert editor_token in created_message
