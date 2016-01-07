# -*- coding: utf-8 -*-
from os.path import dirname, join
from mock import Mock
from pyramid.testing import DummyRequest, setUp, tearDown
from pytest import fixture
from tempfile import mkdtemp
from urllib import unquote
from webtest import TestApp


settings = {
    'smtp': Mock(),
    'fs_pgp_pubkeys': join(dirname(__file__), 'tests', 'gpghome'),
    'editors': ['editor@briefkasten.dtfh.de'],
    'admins': ['admin@briefkasten.dtfh.de'],
    'appserver_root_url': '/briefkasten/',
    'fs_dropbox_root': mkdtemp(),
    'fs_bin_path': join(dirname(__file__), 'bin'),
    'mail.default_sender': 'noreply@briefkasten.dtfh.de',
}


@fixture()
def config(request):
    """ Sets up a Pyramid `Configurator` instance suitable for testing. """
    config = setUp(settings=settings)
    request.addfinalizer(tearDown)
    return config


@fixture
def app(config):
    """ Returns WSGI application wrapped in WebTest's testing interface. """
    from . import configure
    return configure({}, **config.registry.settings).make_wsgi_app()


@fixture
def browser(app, request):
    extra_environ = dict(HTTP_HOST='example.com')
    browser = TestApp(app, extra_environ=extra_environ)
    return browser


@fixture
def dummy_request(config):
    return DummyRequest()


@fixture(scope='session')
def testing():
    """ Returns the `testing` module. """
    from sys import modules
    return modules[__name__]    # `testing.py` has already been imported


def route_url(name, **kwargs):
    return unquote(DummyRequest().route_url(name, **kwargs))
