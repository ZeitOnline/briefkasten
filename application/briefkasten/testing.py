# -*- coding: utf-8 -*-
import shutil
from cgi import FieldStorage
from os.path import abspath, dirname, join
from mock import Mock
from pyramid.testing import DummyRequest, setUp, tearDown
from pytest import fixture
from urllib import unquote
from webtest import TestApp


def asset_path(*parts):
    return abspath(join(dirname(__file__), 'tests', *parts))


@fixture(scope="function")
def dropbox_container(request, tmpdir):
    from briefkasten.dropbox import DropboxContainer
    # initialize empty directory with settings from template:
    shutil.copy(
        join(asset_path('drop_root_template', 'settings.yaml')),
        tmpdir.strpath,
    )
    dropbox_container = DropboxContainer(
        root=tmpdir.strpath,
        settings=dict(
            smtp=Mock(),
            fs_bin_path=asset_path('bin'),
        ),
    )
    request.addfinalizer(dropbox_container.destroy)
    return dropbox_container


@fixture
def settings(dropbox_container):
    return {
        'appserver_root_url': '/briefkasten/',
        'fs_dropbox_root': dropbox_container.fs_path,
        'fs_pgp_pubkeys': asset_path('gpghome'),
        'fs_bin_path': asset_path('bin'),
        'post_secret': u's3cr3t',
    }


@fixture()
def config(request, settings):
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
