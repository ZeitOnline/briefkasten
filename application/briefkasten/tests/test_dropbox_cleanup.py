from os import listdir
from pytest import fixture


@fixture
def cleansed_dropbox(dropbox_container, dropbox):
    """ TBD"""
    pass


def test_initial_backup(dropbox_container, dropbox):
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)


def test_initial_backup_removed_on_cleanup_after_success(dropbox_container, dropbox):
    dropbox._create_backup()
    assert 'dirty.zip.pgp' in listdir(dropbox.fs_path)
    dropbox.cleanup()
    assert 'dirty.zip.pgp' not in listdir(dropbox.fs_path)
