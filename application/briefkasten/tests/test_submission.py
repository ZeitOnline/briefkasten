# -*- coding: utf-8 -*-
from os import listdir
from os.path import join, dirname
from pytest import fixture
from webtest import Upload


@fixture(scope="function")
def submit_url(testing, post_token):
    return testing.route_url('dropbox_form_submit', token=post_token)


@fixture(scope="function")
def upload_url(testing, post_token):
    return testing.route_url('dropbox_fileupload', token=post_token)


def test_successful_submission(browser, submit_url):
    response = browser.post(submit_url, params=dict(message=u'hey'))
    assert response.status == '302 Found'
    browser.get(response.location)


@fixture
def form(testing, browser):
    return browser.get(testing.route_url('dropbox_form')).forms[0]


def test_submission_with_one_attachment_post(testing, dropbox_container, form):
    fs_attachment = testing.asset_path('attachment.txt')
    assert len(listdir(dropbox_container.fs_path)) == 0
    form.set(
        'upload',
        Upload(
            'attachment.txt',
            open(fs_attachment, 'r').read(),
            'text/plain'),
        index=0)
    form['message'] = 'Hello there'
    form.submit()


def test_upload_attachment_directly(testing, dropbox_container, browser, upload_url, submit_url):
    """clients can also upload files directly, i.e. w/o submitting the form.
    files uploaded like this will be stored in the dropbox."""
    fs_attachment = testing.asset_path('attachment.txt')
    browser.post(
        upload_url,
        params=dict(
            attachment=Upload(
                'attachment.txt',
                open(fs_attachment, 'r').read(),
                'text/plain'),
        ),
    )
    fs_dropbox = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0])
    assert len(listdir(join(fs_dropbox, 'attach'))) == 1
    fs_attachments = join(
        dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'attach')
    fs_attachment = join(fs_attachments, listdir(fs_attachments)[0])
    assert open(fs_attachment).read().decode('utf-8') == \
        open(fs_attachment, 'r').read().decode('utf-8')


def test_submission_with_multiple_attachments(dropbox_container, form):
    form.set(
        'upload',
        Upload(
            'attachment.txt',
            open(join(dirname(__file__), 'attachment.txt'), 'r').read(),
            'text/plain'),
        index=0)
    form['message'] = 'Hello there'
    form.submit()
