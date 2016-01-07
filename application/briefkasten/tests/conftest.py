# -*- coding: utf-8 -*-
from os.path import dirname, join
from mock import Mock
from pytest import fixture
from tempfile import mkdtemp
from webtest import TestApp


from briefkasten import main


@fixture
def smtp():
    return Mock()


@fixture
def settings(smtp):
    settings = dict(
        smtp=smtp,
        fs_pgp_pubkeys=join(dirname(__file__), 'gpghome'),
        editors=['editor@briefkasten.dtfh.de'],
        admins=['admin@briefkasten.dtfh.de'],
        appserver_root_url='/briefkasten/',
        fs_dropbox_root=mkdtemp(),
        fs_bin_path=join(dirname(__file__), 'bin')
    )
    settings['mail.default_sender'] = 'noreply@briefkasten.dtfh.de'
    return settings


@fixture
def app(request, settings):
    return main(
        dict(),
        **settings
    )


@fixture
def browser(app, request):
    """ Returns an instance of `webtest.TestApp`.  The `user` pytest marker
        (`pytest.mark.user`) can be used to pre-authenticate the browser
        with the given login name: `@user('admin')`. """
    extra_environ = dict(HTTP_HOST='example.com')
    browser = TestApp(app, extra_environ=extra_environ)
    return browser
