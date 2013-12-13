# -*- coding: utf-8 -*-
from briefkasten import dropbox_container


def test_non_existent_drop_id_raises_not_found(browser):
    response = browser.get('/briefkasten/foobar', status=404)
    assert response.status == '404 Not Found'


def test_submitter_views_reply(browser):
    dropbox = dropbox_container.add_dropbox(message=u'Hello')
    reply = u'Good bye und schöne Grüße.'
    author = u'John Doe'
    dropbox.add_reply(dict(reply=reply, author=author))
    response = browser.get('/briefkasten/%s' % dropbox.drop_id)
    response.mustcontain(reply)
    response.mustcontain(author)
