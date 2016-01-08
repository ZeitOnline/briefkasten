# -*- coding: utf-8 -*-
from cgi import FieldStorage
from os.path import abspath, dirname, join
from mock import Mock
from pyramid.testing import DummyRequest, setUp, tearDown
from pytest import fixture
from tempfile import mkdtemp
from urllib import unquote
from webtest import TestApp


def asset_path(*parts):
    return abspath(join(dirname(__file__), 'tests', *parts))


settings = {
    'smtp': Mock(),
    'fs_pgp_pubkeys': asset_path('gpghome'),
    'editors': ['editor@briefkasten.dtfh.de'],
    'admins': ['admin@briefkasten.dtfh.de'],
    'appserver_root_url': '/briefkasten/',
    'fs_dropbox_root': mkdtemp(),
    'fs_bin_path': asset_path('bin'),
    'mail.default_sender': 'noreply@briefkasten.dtfh.de',
    'post_secret': u's3cr3t',
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


def attachment_factory(**kwargs):
    a = FieldStorage()
    for key, value in kwargs.items():
        setattr(a, key, value)
    return a
