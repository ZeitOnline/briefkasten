# -*- coding: utf-8 -*-
from os import listdir
from os.path import join, dirname, exists
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


def test_submission_without_attachment_or_message(testing, dropbox_container, form):
    form.submit()


def test_submission_without_attachment_post(testing, dropbox_container, form):
    assert len(listdir(dropbox_container.fs_path)) == 0
    form['message'] = u'Hellø there'
    form.submit()
    assert len(listdir(dropbox_container.fs_path)) == 1
    created_drop_id = listdir(dropbox_container.fs_path)[0]
    fs_dropbox_status = join(dropbox_container.fs_path, created_drop_id, 'status')
    assert open(fs_dropbox_status).read() == u'020 submitted'
    fs_dropbox_submission = join(dropbox_container.fs_root, 'submissions', created_drop_id)
    assert exists(fs_dropbox_submission)


def test_submission_with_one_attachment_post(testing, dropbox_container, form):
    fs_attachment = testing.asset_path('attachment.txt')
    assert len(listdir(dropbox_container.fs_path)) == 0
    form.set(
        'upload',
        Upload(
            'attachment.txt',
            open(fs_attachment, 'rb').read(),
            'text/plain'),
        index=0)
    form['message'] = 'Hello there'
    form.submit()
    assert len(listdir(dropbox_container.fs_path)) == 1
    fs_dropbox_status = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0], 'status')
    assert open(fs_dropbox_status).read() == u'020 submitted'


def test_upload_attachment_directly(testing, dropbox_container, browser, upload_url, submit_url):
    """clients can also upload files directly, i.e. w/o submitting the form.
    files uploaded like this will be stored in the dropbox."""
    fs_attachment = testing.asset_path('attachment.txt')
    browser.post(
        upload_url,
        params=dict(
            attachment=Upload(
                'attachment.txt',
                open(fs_attachment, 'rb').read(),
                'text/plain'),
        ),
    )
    fs_dropbox = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0])
    # we have one attachment:
    assert len(listdir(join(fs_dropbox, 'attach'))) == 1
    fs_attachments = join(
        dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'attach')
    fs_attachment = join(fs_attachments, listdir(fs_attachments)[0])
    # its contents is still unencrypted:
    assert open(fs_attachment).read() == \
        open(fs_attachment, 'r').read()


@fixture
def post_token_dropbox(dropbox_container, config, post_token):
    """ returns a dropbox instance matching the given post_token"""
    from briefkasten import parse_post_token
    return dropbox_container.get_dropbox(
        parse_post_token(
            post_token,
            secret=config.registry.settings['post_secret']
        )
    )


def test_upload_attachment_directly_fails_post_submission(testing, dropbox_container, browser, post_token_dropbox, upload_url):
    """clients cannot upload files directly once a dropbox has been submitted. """
    post_token_dropbox.status = u'020 submitted'
    fs_attachment = testing.asset_path('attachment.txt')
    browser.post(
        upload_url,
        params=dict(
            attachment=Upload(
                'attachment.txt',
                open(fs_attachment, 'rb').read(),
                'text/plain'),
        ),
        status=410,
    )


def test_submission_with_multiple_attachments(dropbox_container, form):
    form.set(
        'upload',
        Upload(
            'attachment.txt',
            open(join(dirname(__file__), 'attachment.txt'), 'rb').read(),
            'text/plain'),
        index=0)
    form['message'] = 'Hello there'
    form.submit()
