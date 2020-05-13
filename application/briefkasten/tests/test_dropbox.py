# -*- coding: utf-8 -*-
import hashlib
import os
import stat
from os.path import dirname, exists, join


def test_dropbox_is_created_if_it_does_not_exist():
    from shutil import rmtree
    # assemble a 'safe' directory location inside our package
    # and make sure it does not exist
    dropbox_root = join(dirname(__file__), '__test__dropbox_root__')
    if exists(dropbox_root):
        rmtree(dropbox_root)

    # instantiating our application will cause the specified directory
    # to be created
    assert not exists(dropbox_root)
    from briefkasten.dropbox import DropboxContainer
    DropboxContainer(root=dropbox_root, settings=dict(fs_pgp_pubkeys=None))
    assert exists(dropbox_root)
    # clean up after ourselves
    rmtree(dropbox_root)


def test_dropbox_status_no_message(dropbox_container):
    dropbox = dropbox_container.add_dropbox(drop_id=u'foo')
    assert dropbox.status == u'010 created'


def test_dropbox_status_no_file(dropbox):
    os.remove(join(dropbox.fs_path, 'status'))
    assert dropbox.status == u'000 no status file'


def test_dropbox_status_manual(dropbox):
    with open(join(dropbox.fs_path, 'status'), 'w') as status_file:
        status_file.write(u'23 in limbo')
    assert dropbox.status == u'23 in limbo'


def test_dropbox_status_initial(dropbox):
    """ the initial status of a dropbox is 'created'"""
    assert dropbox.status == u'010 created'


def test_dropbox_status_submitted_without_attachment(dropbox_without_attachment):
    """a dropbox without an attachment won't be cleansed and will be set to 'success' directly
       after processing"""
    dropbox_without_attachment.process()
    assert dropbox_without_attachment.status == u'900 success'


def test_dropbox_status_submitted(dropbox):
    """once a dropbox has initiated its processing, its status changes to 'quarantined',
    however, in our test setup this always succeeds immediately.
    """
    dropbox.process()
    assert dropbox.status == u'900 success'


def test_mocked_attachment_processor_status(dropbox):
    dropbox._process_attachments()
    assert dropbox.status == u'299 Cleansed'


def test_mocked_attachment_processor_cleansed(dropbox):
    fs_dirty = dropbox.fs_dirty_attachments[0]
    dirty_lines = open(fs_dirty, 'r').readlines()
    dropbox._process_attachments()
    fs_cleansed = dropbox.fs_cleansed_attachments[0]
    assert open(fs_cleansed, 'r').readlines() == dirty_lines


def test_dropbox_process_failure(dropbox):
    # TODO
    pass


def test_dropbox_retrieval(dropbox_container, dropbox):
    assert dropbox.drop_id == dropbox_container.get_dropbox(dropbox.drop_id).drop_id
    assert dropbox.editor_token == dropbox_container.get_dropbox(dropbox.drop_id).editor_token
    assert dropbox.message == dropbox_container.get_dropbox(dropbox.drop_id).message


def test_dropbox_permissions(dropbox):
    assert stat.S_IMODE(os.stat(dropbox.paths_created[0]).st_mode) == 0o770


def test_message_permissions(dropbox):
    assert stat.S_IMODE(os.stat(dropbox.paths_created[1]).st_mode) == 0o660


def test_editor_token_created(dropbox_container, dropbox):
    assert (dropbox_container.get_dropbox(
        dropbox.drop_id).editor_token ==
        open(dropbox.paths_created[1], 'r').readline())
    assert stat.S_IMODE(os.stat(dropbox.paths_created[1]).st_mode) == 0o660


def test_attachment_creation_and_permissions(dropbox_container, drop_id, testing):
    attachment = testing.attachment_factory(**{
        'file': open(testing.asset_path('attachment.txt'), 'rb'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'attachment.txt',
        'size': -1})
    dropbox = dropbox_container.add_dropbox(drop_id, message=u'Überraschung!', attachments=[attachment])
    assert stat.S_IMODE(os.stat(dropbox.paths_created[-2]).st_mode) == 0o770
    assert dropbox.paths_created[-2].endswith("/attach")
    assert stat.S_IMODE(os.stat(dropbox.paths_created[-1]).st_mode) == 0o660
    # we strip the original filename
    assert not dropbox.paths_created[-1].endswith("/attach/attachment.txt")
    # but preserve the file ending
    assert dropbox.paths_created[-1].endswith(".txt")
    assert open(dropbox.paths_created[-1]).read() == u'Schönen Guten Tag!'  # contents of attachment.txt


def test_attachment_creation_outside_container(dropbox_container, drop_id, testing):
    attachment = testing.attachment_factory(**{
        'file': open(testing.asset_path('attachment.txt'), 'rb'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'../../authorized_keys',
        'size': -1})
    dropbox_container.add_dropbox(drop_id, message=u'Überraschung!', attachments=[attachment])
    assert not exists(join(dropbox_container.fs_path, 'authorized_keys'))


md5 = hashlib.md5()


def md5sum(f):
    for chunk in iter(lambda: f.read(8192), b''):
        md5.update(chunk)
    return md5.digest()


def test_attachment_is_image(dropbox_container, drop_id, testing):
    attachment = testing.attachment_factory(**{
        'file': open(testing.asset_path('attachment.png'), 'rb'),
        'mimetype': 'image/jpeg',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'attachment.png',
        'size': -1})
    dropbox = dropbox_container.add_dropbox(drop_id, message=u'Mit Foto', attachments=[attachment])
    # we strip the original filename
    assert not dropbox.paths_created[-1].endswith("/attach/attachment.png")
    # but preserve the file ending
    assert dropbox.paths_created[-1].endswith(".png")
    assert md5sum(open(dropbox.paths_created[-1], 'rb')) == md5sum(attachment.file)


def test_attachment_is_unicode(dropbox_container, drop_id, testing):
    attachment = testing.attachment_factory(**{
        'file': open(testing.asset_path('unicode.txt'), 'rb'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'unicode.txt',
        'size': -1})
    # we only assert that this works
    dropbox_container.add_dropbox(drop_id, message=u'Überraschung!', attachments=[attachment])


def test_non_existent_drop_id_creates_dropbox_ad_hoc(dropbox_container):
    assert 'foobar' not in dropbox_container
    newbox = dropbox_container.get_dropbox('foobar')
    assert newbox.drop_id == 'foobar'
    assert 'foobar' in dropbox_container


def test_add_one_reply(dropbox_container, dropbox):
    reply = dict(
        message=u'Smørebrød',
        author=u'Børk')
    dropbox.add_reply(reply)
    assert dropbox.replies[0]['message'] == u'Smørebrød'
    assert dropbox.replies[0]['author'] == u'Børk'
    refetched_dropbox = dropbox_container.get_dropbox(dropbox.drop_id)
    assert refetched_dropbox.replies[0]['message'] == u'Smørebrød'
    assert refetched_dropbox.replies[0]['author'] == u'Børk'


def test_add_two_replies(app):
    NotImplemented


def test_access_replies(app):
    NotImplemented


def test_dropid_length():
    from briefkasten.dropbox import generate_drop_id
    assert len(generate_drop_id(12)) == 12


def test_filename_sanitizing():
    from briefkasten.dropbox import sanitize_filename
    assert not sanitize_filename('attachment.txt') == 'attachment.txt'
    assert sanitize_filename('attachment.txt').endswith('.txt')


def test_filename_has_no_ending():
    from briefkasten.dropbox import sanitize_filename
    assert not sanitize_filename('blubber') == 'blubber'


def test_drop_url(dropbox, app, testing):
    assert dropbox.drop_url == testing.route_url('dropbox_view', drop_id=dropbox.drop_id)


def test_editor_url(dropbox, app, testing):
    assert dropbox.editor_url == testing.route_url(
        'dropbox_editor',
        drop_id=dropbox.drop_id,
        editor_token=dropbox.editor_token)


def test_notification_text_message(dropbox_without_attachment):
    message = u'Sätz mit Ümlœuten'
    dropbox_without_attachment.message = message
    assert message in dropbox_without_attachment._notification_text


def test_notification_text_zero(dropbox_without_attachment):
    assert u'Die Einreichung enthielt keine Anhänge.' in dropbox_without_attachment._notification_text


def test_notification_text_one(dropbox):
    assert u'Die Einreichung enthielt einen Anhang' in dropbox._notification_text


def test_notification_text_unsupported(dropbox):
    dropbox.status = '800 unsupported file type'
    assert u'Mindestens ein Anhang wurde nicht bereinigt, da dessen Dateityp nicht unterstützt wird.' in dropbox._notification_text


def test_notification_text_two(dropbox, testing):
    attachment = testing.attachment_factory(**{
        'file': open(testing.asset_path('unicode.txt'), 'rb'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'unicode.txt',
        'size': -1})
    dropbox.add_attachment(attachment)
    assert u'Die Einreichung enthielt 2 Anhänge.' in dropbox._notification_text


def test_dirty_archive_url(dropbox, app, testing):
    assert dropbox.dirty_archive_url is not None


def test_dirty_archive_url_without_format(dropbox, app, testing):
    del dropbox.settings['dropbox_dirty_archive_url_format']
    assert dropbox.dirty_archive_url is None
