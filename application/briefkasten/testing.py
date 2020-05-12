# -*- coding: utf-8 -*-
import shutil
from cgi import FieldStorage
from jinja2 import Environment, FileSystemLoader
from os.path import abspath, dirname, join
from mock import Mock
from pyramid.testing import DummyRequest, setUp, tearDown
from pytest import fixture
from urllib.parse import unquote
from webtest import TestApp


def asset_path(*parts):
    return abspath(join(dirname(__file__), 'tests', *parts))


jinja_env = Environment(
    loader=FileSystemLoader(asset_path()))


@fixture(scope="function")
def gpghome(tmpdir):
    fs_gpghome = join(tmpdir.strpath, 'gpghome')
    shutil.copytree(asset_path('gpghome'), fs_gpghome)
    return fs_gpghome


@fixture(scope="function")
def dropbox_container(request, tmpdir, gpghome):
    from briefkasten.dropbox import DropboxContainer
    # initialize empty directory with settings from template:
    fs_drop_root = tmpdir.strpath
    with open(join(fs_drop_root, 'settings.yaml'), 'w') as fs_settings:
        fs_settings.write(
            jinja_env.get_template('drop_root_template/settings.yaml').render(
                fs_pgp_pubkeys=gpghome
            )
        )
    dropbox_container = DropboxContainer(
        root=fs_drop_root,
        settings=dict(
            smtp=Mock(),
            fs_bin_path=asset_path('bin'),
        ),
    )
    request.addfinalizer(dropbox_container.destroy)
    return dropbox_container


@fixture
def settings(dropbox_container, gpghome):
    return {
        'appserver_root_url': '/briefkasten/',
        'fs_dropbox_root': dropbox_container.fs_root,
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
