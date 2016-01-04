# -*- coding: utf-8 -*-
import hashlib
import os
import stat
from os.path import dirname, exists, join
from tempfile import mkdtemp

from pytest import fixture, raises


#
# tempfile store tests
#


@fixture(scope='function')
def dropbox_container(request):
    from briefkasten.dropbox import DropboxContainer
    dropbox_container = DropboxContainer(dict(fs_dropbox_root=mkdtemp(),
        fs_bin_path=join(dirname(__file__), 'bin')
    ))
    request.addfinalizer(dropbox_container.destroy)
    return dropbox_container


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
    DropboxContainer(dict(fs_dropbox_root=dropbox_root))
    assert exists(dropbox_root)
    # clean up after ourselves
    rmtree(dropbox_root)


@fixture
def dropbox_without_attachment(dropbox_container):
    return dropbox_container.add_dropbox(message=u'Schönen guten Tag!')


@fixture
def dropbox(dropbox_container):
    open(join(dirname(__file__), 'attachment.txt'), 'r')
    return dropbox_container.add_dropbox(
        message=u'Schönen guten Tag!',
        attachments=[
            dict(
                filename=u'attachment.txt',
                fp=open(join(dirname(__file__), 'attachment.txt'), 'r')
            )
        ])


def test_dropbox_status_no_message(dropbox_container):
    dropbox = dropbox_container.add_dropbox(
        drop_id=u'foo',
        force_create=True
    )
    assert dropbox.status == u'001 initialised'


def test_dropbox_status_no_file(dropbox):
    os.remove(join(dropbox.fs_path, 'status'))
    assert dropbox.status == u'000 no status file'


def test_dropbox_status_manual(dropbox):
    with open(join(dropbox.fs_path, 'status'), 'w') as status_file:
            status_file.write(u'23 in limbo'.encode('utf-8'))
    assert dropbox.status == u'23 in limbo'


def test_dropbox_status_initial(dropbox):
    """ the initial status of a dropbox is 'created'"""
    assert dropbox.status == u'010 created'


def test_dropbox_status_submitted_without_attachment(dropbox_without_attachment):
    """a dropbox without an attachment won't be cleansed and will be set to 'success' directly
       after processing"""
    dropbox_without_attachment.process()
    assert dropbox_without_attachment.status == u'090 sucess'


def test_dropbox_status_submitted(dropbox):
    """once a dropbox has initiated its processing, its status changes to 'quarantined'"""
    dropbox.process()
    assert dropbox.status == u'020 submitted'


def test_dropbox_process_failure(dropbox):
    import pdb; pdb.set_trace()


def test_dropbox_retrieval(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!',
        attachments=[dict(fp=open(join(dirname(__file__), 'attachment.txt'), 'r'),
        mime_type='text/plain',
        filename=u'fööbar.txt')])
    assert dropbox.drop_id == dropbox_container.get_dropbox(dropbox.drop_id).drop_id
    assert dropbox.editor_token == dropbox_container.get_dropbox(dropbox.drop_id).editor_token
    # the message itself is not stored on the fs!
    with raises(AttributeError):
        assert dropbox.message == dropbox_container.get_dropbox(dropbox.drop_id).message


def test_dropbox_permissions(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!')
    assert stat.S_IMODE(os.stat(dropbox.paths_created[0]).st_mode) == 0770


def test_message_permissions(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!')
    assert stat.S_IMODE(os.stat(dropbox.paths_created[1]).st_mode) == 0660


def test_editor_token_created(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!')
    assert (dropbox_container.get_dropbox(dropbox.drop_id).editor_token ==
        open(dropbox.paths_created[2], 'r').readline())
    assert stat.S_IMODE(os.stat(dropbox.paths_created[2]).st_mode) == 0660


def test_attachment_creation_and_permissions(dropbox_container):
    attachment = {
        'fp': open(os.path.join(os.path.dirname(__file__), 'attachment.txt'), 'r'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'attachment.txt',
        'size': -1}
    dropbox = dropbox_container.add_dropbox(message=u'Überraschung!', attachments=[attachment])
    assert stat.S_IMODE(os.stat(dropbox.paths_created[2]).st_mode) == 0770
    assert dropbox.paths_created[2].endswith("/attach")
    assert stat.S_IMODE(os.stat(dropbox.paths_created[3]).st_mode) == 0660
    # we strip the original filename
    assert not dropbox.paths_created[3].endswith("/attach/attachment.txt")
    # but preserve the file ending
    assert dropbox.paths_created[3].endswith(".txt")
    assert open(dropbox.paths_created[3]).read().decode('utf-8') == u'Schönen Guten Tag!'  # contents of attachment.txt


def test_attachment_creation_outside_container(dropbox_container):
    attachment = {
        'fp': open(os.path.join(os.path.dirname(__file__), 'attachment.txt'), 'r'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'../../authorized_keys',
        'size': -1}
    dropbox_container.add_dropbox(message=u'Überraschung!', attachments=[attachment])
    assert not exists(join(dropbox_container.fs_path, 'authorized_keys'))


md5 = hashlib.md5()


def md5sum(f):
    for chunk in iter(lambda: f.read(8192), b''):
        md5.update(chunk)
    return md5.digest()


def test_attachment_is_image(dropbox_container):
    attachment = {
        'fp': open(os.path.join(os.path.dirname(__file__), 'attachment.png'), 'rb'),
        'mimetype': 'image/jpeg',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'attachment.png',
        'size': -1}
    dropbox = dropbox_container.add_dropbox(message=u'Mit Foto', attachments=[attachment])
    # we strip the original filename
    assert not dropbox.paths_created[3].endswith("/attach/attachment.png")
    # but preserve the file ending
    assert dropbox.paths_created[3].endswith(".png")
    assert md5sum(open(dropbox.paths_created[3], 'rb')) == md5sum(attachment['fp'])


def test_attachment_is_unicode(dropbox_container):
    attachment = {
        'fp': open(os.path.join(os.path.dirname(__file__), 'unicode.txt'), 'r'),
        'mimetype': 'text/plain',
        'uid': 'foobar',
        'preview_url': None,
        'filename': u'unicode.txt',
        'size': -1}
    dropbox_container.add_dropbox(message=u'Überraschung!', attachments=[attachment])


def test_non_existent_drop_id_raises_error(dropbox_container):
    with raises(KeyError):
        dropbox_container.get_dropbox('foobar')


def test_add_one_reply(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!')
    reply = dict(message=u'Smørebrød',
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


def test_process_script(dropbox_container):
    dropbox = dropbox_container.add_dropbox(message=u'Schönen guten Tag!')
    assert dropbox.process() == 0


def test_filename_sanitizing():
    from briefkasten.dropbox import sanitize_filename
    assert not sanitize_filename('attachment.txt') == 'attachment.txt'
    assert sanitize_filename('attachment.txt').endswith('.txt')


def test_filename_has_no_ending():
    from briefkasten.dropbox import sanitize_filename
    assert not sanitize_filename('blubber') == 'blubber'
