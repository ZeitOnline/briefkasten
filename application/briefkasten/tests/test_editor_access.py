# -*- coding: utf-8 -*-
from briefkasten import dropbox_container


def test_incorrect_token_raises_not_found(browser):
    dropbox = dropbox_container.add_dropbox(message=u'Hello')
    response = browser.get('/briefkasten/%s/xxxx' % dropbox.drop_id, status=404)
    assert response.status == '404 Not Found'


def test_correct_token(browser):
    dropbox = dropbox_container.add_dropbox(message=u'Hello')
    response = browser.get('/briefkasten/%s/%s' % (dropbox.drop_id, dropbox.editor_token))
    assert response.status == '200 OK'


def test_editor_posts_reply(browser):
    dropbox = dropbox_container.add_dropbox(message=u'Hello')
    reply = u'How do you do?'
    author = u'John Doe'
    page = browser.get('/briefkasten/%s/%s' % (dropbox.drop_id, dropbox.editor_token))
    form = page.forms['deform']
    form['reply'] = reply
    form['author'] = author
    form.submit()
    refetched_dropbox = dropbox_container.get_dropbox(dropbox.drop_id)
    assert refetched_dropbox != dropbox
    assert refetched_dropbox.replies[0]['reply'] == reply
    assert refetched_dropbox.replies[0]['author'] == author


def test_editor_posts_empty_reply(browser):
    dropbox = dropbox_container.add_dropbox(message=u'Hello')
    browser.get('/briefkasten/%s/%s' % (dropbox.drop_id, dropbox.editor_token)).forms[0].submit()
    assert dropbox.replies == []
