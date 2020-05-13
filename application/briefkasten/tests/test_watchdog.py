# -*- coding: utf-8 -*-
from pytest import fixture
from os import listdir


def test_dropbox_is_marked_as_not_watchdog_submission(dropbox):
    assert not dropbox.from_watchdog


def test_dropbox_is_marked_as_watchdog_submission(watchdog_dropbox):
    assert watchdog_dropbox.from_watchdog


def test_non_watchdog_dropbox_editors(dropbox, dropbox_container):
    assert dropbox.editors == dropbox_container.settings['editors']


def test_watchdog_dropbox_editors(watchdog_dropbox, dropbox_container):
    assert watchdog_dropbox.editors == [dropbox_container.settings['watchdog_imap_recipient']]


def test_dropbox_is_marked_as_watchdog_submission_post_init(dropbox_container, dropbox):
    dropbox.from_watchdog = True
    # refetch and check
    assert dropbox_container.get_dropbox(dropbox.drop_id).from_watchdog


def test_dropbox_is_unmarked_as_watchdog_submission_post_init(dropbox_container, watchdog_dropbox):
    watchdog_dropbox.from_watchdog = False
    # refetch and check
    assert not dropbox_container.get_dropbox(watchdog_dropbox.drop_id).from_watchdog


@fixture
def form(testing, browser):
    return browser.get(testing.route_url('dropbox_form')).forms[0]


def test_watchdog_submits_with_invalid_secret(testing, dropbox_container, form):
    form['message'] = 'Hellø there'
    form['testing_secret'] = 'xxx'
    form.submit()
    created_drop = dropbox_container.get_dropbox(listdir(dropbox_container.fs_path)[0])
    assert not created_drop.from_watchdog


def test_watchdog_submits_with_valid_secret(testing, dropbox_container, form):
    form['message'] = 'Hellø there'
    form['testing_secret'] = dropbox_container.settings['test_submission_secret']
    form.submit()
    created_drop = dropbox_container.get_dropbox(listdir(dropbox_container.fs_path)[0])
    assert created_drop.from_watchdog
