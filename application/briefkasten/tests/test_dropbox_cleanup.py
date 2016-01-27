from os import listdir, mkdir
from os.path import join
from pytest import fixture


@fixture
def cleansed_dropbox(dropbox_container, dropbox):
    mkdir(join(dropbox.fs_path, 'clean'))
    return dropbox


def test_cleanup_deletes_message(dropbox_container, dropbox):
    assert 'message' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'message' not in listdir(dropbox.fs_path)


def test_cleanup_deletes_dirty_attachments(dropbox_container, dropbox):
    assert 'attach' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'attach' not in listdir(dropbox.fs_path)


def test_cleanup_deletes_cleansed_attachments(dropbox_container, cleansed_dropbox):
    assert 'clean' in listdir(cleansed_dropbox.fs_path)
    cleansed_dropbox.cleanup()
    assert 'clean' not in listdir(cleansed_dropbox.fs_path)


def test_initial_backup_creation(dropbox_container, dropbox):
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)


def test_initial_backup_removed_on_cleanup(dropbox_container, dropbox):
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)
