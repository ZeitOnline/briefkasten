from os import listdir
from os.path import join, dirname


def test_visit_fingerprint(browser):
    response = browser.get('/briefkasten/fingerprint')
    response.status == '200 OK'


def test_successful_submission(browser):
    response = browser.post('/briefkasten/submit', params=dict(message=u'hey'))
    response.status == '200 OK'


def test_submission_validation_failure(browser):
    response = browser.post('/briefkasten/submit', params=dict(message=u''))
    response.status == '200 OK'


def test_submission_with_one_attachment_post(zbrowser):
    from briefkasten import dropbox_container
    assert len(listdir(dropbox_container.fs_path)) == 0
    zbrowser.getControl(name='upload', index=0).add_file(open(join(dirname(__file__), 'attachment.txt'), 'r').read(),
        'text/plain', 'attachment.txt')
    zbrowser.getControl(name='message').value = 'Hello there'
    zbrowser.getForm(index=1).submit()
    fs_dropbox = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0])
    assert len(listdir(join(fs_dropbox, 'attach'))) == 1
    fs_attachment = join(dropbox_container.fs_path,
        listdir(dropbox_container.fs_path)[0], 'attach', 'attachment.txt')
    assert open(fs_attachment).read().decode('utf-8') == open(join(dirname(__file__), 'attachment.txt'), 'r').read().decode('utf-8')


def test_submission_with_multiple_attachments(zbrowser):
    from briefkasten import dropbox_container, views
    # patch the default number of attachments, since the zbrowser cannot execute javascript
    views.attachments_min_len = 2
    zbrowser.reload()  # need to reload for change to take effect
    zbrowser.getControl(name='upload', index=0).add_file(open(join(dirname(__file__), 'attachment.txt'), 'r').read(),
        'text/plain', 'attachment.txt')
    zbrowser.getControl(name='upload', index=1).add_file(open(join(dirname(__file__), 'attachment.png'), 'r').read(),
        'image/png', 'attachment.png')
    zbrowser.getControl(name='message').value = 'Hello there'
    zbrowser.getForm(index=1).submit()
    fs_dropbox = join(dropbox_container.fs_path, listdir(dropbox_container.fs_path)[0])
    assert len(listdir(join(fs_dropbox, 'attach'))) == 2
    fs_attachment = join(fs_dropbox, 'attach', 'attachment.txt')
    assert open(fs_attachment).read().decode('utf-8') == open(join(dirname(__file__), 'attachment.txt'), 'r').read().decode('utf-8')
    fs_attachment = join(fs_dropbox, 'attach', 'attachment.png')
