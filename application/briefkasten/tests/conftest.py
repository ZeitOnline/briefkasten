# -*- coding: utf-8 -*-
from pytest import fixture
from os.path import dirname, join


@fixture
def post_token(dropbox_container, config):
    from briefkasten import generate_post_token
    return generate_post_token(secret=config.registry.settings['post_secret'])


@fixture
def drop_id(dropbox_container):
    from briefkasten import generate_drop_id
    return generate_drop_id()


@fixture
def dropbox_without_attachment(dropbox_container, drop_id):
    return dropbox_container.add_dropbox(drop_id, message=u'Schönen guten Tag!')


@fixture
def attachment(testing):
    return testing.attachment_factory(
        filename=u'attachment.txt',
        file=open(join(dirname(__file__), 'attachment.txt'), 'rb')
    )


@fixture
def dropbox(dropbox_container, drop_id, attachment):
    return dropbox_container.add_dropbox(
        drop_id,
        message=u'Schönen guten Tag!',
        attachments=[attachment],
    )


@fixture
def watchdog_dropbox(dropbox_container, drop_id, attachment):
    return dropbox_container.add_dropbox(
        drop_id,
        message=u'Schönen guten Tag!',
        attachments=[attachment],
        from_watchdog=True,
    )
