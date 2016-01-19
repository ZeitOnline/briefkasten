# -*- coding: utf-8 -*-
from pytest import fixture


def test_incorrect_token_raises_not_found(testing, browser, dropbox):
    response = browser.get(testing.route_url('dropbox_editor', drop_id=dropbox.drop_id, editor_token='xxx'), status=404)
    assert response.status == '404 Not Found'


@fixture
def editor_url(testing, dropbox):
    return testing.route_url('dropbox_editor', drop_id=dropbox.drop_id, editor_token=dropbox.editor_token)


def test_correct_token(testing, browser, editor_url):
    response = browser.get(editor_url)
    assert response.status == '200 OK'


@fixture
def form(testing, browser, editor_url):
    return browser.get(editor_url).forms[0]


def test_editor_posts_reply(form, dropbox, dropbox_container):
    reply = u'How do you do?'
    author = u'John Doe'
    form['reply'] = reply
    form['author'] = author
    form.submit()
    refetched_dropbox = dropbox_container.get_dropbox(dropbox.drop_id)
    assert refetched_dropbox != dropbox
    assert refetched_dropbox.replies[0]['reply'] == reply
    assert refetched_dropbox.replies[0]['author'] == author


def test_editor_posts_empty_reply(browser, dropbox, editor_url):
    browser.get(editor_url).forms[0].submit()
    assert dropbox.replies == []
