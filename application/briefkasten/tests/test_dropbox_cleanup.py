from os import listdir, mkdir, rename
from os.path import join
from pytest import fixture
import shutil


def test_cleanup_deletes_message(dropbox_container, dropbox):
    assert 'message' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'message' not in listdir(dropbox.fs_path)


def test_cleanup_deletes_dirty_attachments(dropbox_container, dropbox):
    assert 'attach' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'attach' not in listdir(dropbox.fs_path)


def test_initial_backup_creation(dropbox_container, dropbox):
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)


def test_initial_backup_removed_on_cleanup(dropbox_container, dropbox):
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)


@fixture
def cleansed_file_src(testing):
    return testing.asset_path('attachment.txt')


@fixture
def cleansed_dropbox(dropbox_container, dropbox, cleansed_file_src):
    rename(join(dropbox.fs_path, 'attach'), join(dropbox.fs_path, 'clean'))
    mkdir(join(dropbox.fs_path, 'attach'))
    return dropbox


def test_cleanup_deletes_cleansed_attachments(dropbox_container, cleansed_dropbox):
    assert 'clean' in listdir(cleansed_dropbox.fs_path)
    cleansed_dropbox.cleanup()
    assert 'clean' not in listdir(cleansed_dropbox.fs_path)


def test_fs_cleansed_attachments_empty(dropbox_container, dropbox):
    assert dropbox.fs_cleansed_attachments == []


def test_fs_cleansed_attachments(dropbox_container, cleansed_dropbox, cleansed_file_src):
    fs_cleansed = cleansed_dropbox.fs_cleansed_attachments[0]
    assert open(fs_cleansed, 'r').readlines() == open(cleansed_file_src, 'r').readlines()


def test_create_archive(dropbox_container, cleansed_dropbox):
    assert listdir(dropbox_container.fs_archive_cleansed) == []
    cleansed_dropbox._create_archive()
    assert listdir(dropbox_container.fs_archive_cleansed) == ['%s.zip.pgp' % cleansed_dropbox.drop_id]


def test_attachment_size_zero(dropbox):
    assert dropbox.size_attachments == 0


def test_attachment_size_one(cleansed_dropbox):
    assert cleansed_dropbox.size_attachments == 19


@fixture
def second_attachment(dropbox, testing):
    shutil.copy2(testing.asset_path('unicode.txt'), join(dropbox.fs_path, 'attach'))
    return join(dropbox.fs_path, 'attach', 'unicode.txt')


def test_archive_is_not_created_for_small_attachments(dropbox_container, dropbox):
    assert listdir(dropbox_container.fs_archive_cleansed) == []
    dropbox.process()
    assert listdir(dropbox_container.fs_archive_cleansed) == []


def test_archive_is_created_for_large_attachments(dropbox_container, dropbox, second_attachment):
    assert listdir(dropbox_container.fs_archive_cleansed) == []
    dropbox.process()
    assert listdir(dropbox_container.fs_archive_cleansed) == ['%s.zip.pgp' % dropbox.drop_id]


@fixture
def unsupported_attachment(dropbox, testing):
    shutil.copy2(testing.asset_path('unicode.txt'), join(dropbox.fs_path, 'attach', 'unsupported.pages'))
    return join(dropbox.fs_path, 'attach', 'unsupported.pages')


@fixture
def mocked_notify_dropbox(dropbox):
    from mock import MagicMock
    mocked_notify = MagicMock()
    mocked_notify.return_value = 1
    dropbox._notify_editors = mocked_notify
    return dropbox


def test_archive_is_marked_dirty_for_unsupported_attachments(monkeypatch, dropbox_container, mocked_notify_dropbox):
    assert listdir(dropbox_container.fs_archive_cleansed) == []
    monkeypatch.setenv('MOCKED_STATUS_CODE', '800')
    mocked_notify_dropbox.process()
    assert listdir(dropbox_container.fs_archive_cleansed) == []
    assert mocked_notify_dropbox.status_int == 800
    assert listdir(dropbox_container.fs_archive_dirty) == ['%s.zip.pgp' % mocked_notify_dropbox.drop_id]
    mocked_notify_dropbox._notify_editors.assert_called_once_with()


def test_unsupported_attachments_are_not_sent_as_mail_attachments_if_archive(settings, monkeypatch, mocked_notify_dropbox):
    monkeypatch.setenv('MOCKED_STATUS_CODE', '800')
    mocked_notify_dropbox.process()
    assert not mocked_notify_dropbox.send_attachments


def test_unsupported_attachments_are_sent_if_no_archive(settings, monkeypatch, mocked_notify_dropbox):
    del mocked_notify_dropbox.settings['dropbox_dirty_archive_url_format']
    monkeypatch.setenv('MOCKED_STATUS_CODE', '800')
    mocked_notify_dropbox.process()
    assert mocked_notify_dropbox.send_attachments
