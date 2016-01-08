# -*- coding: utf-8 -*-
def test_non_existent_drop_id_raises_not_found(browser):
    response = browser.get('/briefkasten/foobar', status=404)
    assert response.status == '404 Not Found'


def test_submitter_views_reply(testing, browser, dropbox):
    reply = u'Good bye und schöne Grüße.'
    author = u'John Doe'
    dropbox.add_reply(dict(reply=reply, author=author))
    response = browser.get(testing.route_url('dropbox_view', drop_id=dropbox.drop_id))
    response.mustcontain(reply)
    response.mustcontain(author)
