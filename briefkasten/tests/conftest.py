# -*- coding: utf-8 -*-
from os.path import dirname, join
from tempfile import mkdtemp
from webtest import TestApp
from wsgi_intercept import add_wsgi_intercept, zope_testbrowser

from briefkasten import main


#
# functional tests with an isolated, temporary dropbox
#
def setup_dropbox():
    fs_dropbox_root = mkdtemp()
    return main({},
        appserver_root_url='/briefkasten/',
        fs_dropbox_root=fs_dropbox_root,
        fs_bin_path=join(dirname(__file__), 'bin')
    )


def teardown_dropbox(test_app):
    from briefkasten import dropbox_container
    dropbox_container.destroy()


def pytest_funcarg__app(request):
    return request.cached_setup(
        setup=setup_dropbox,
        teardown=teardown_dropbox,
        scope="function",
    )


#
# webtest based browser tests
#
def setup_browser_with_dropbox():
    return TestApp(setup_dropbox())


def teardown_browser_with_dropbox(browser):
    teardown_dropbox(browser.app)


def pytest_funcarg__browser(request):
    return request.cached_setup(
        setup=setup_browser_with_dropbox,
        teardown=teardown_browser_with_dropbox,
        scope="function",
    )


#
# zope.testbrowser based browser tests
#
class WSGI_Browser(zope_testbrowser.WSGI_Browser):
    """Allows storing an app instance, so it can be
    torn down."""
    app = None


def setup_zopetestbrowser():
    app = setup_dropbox()
    add_wsgi_intercept('localhost', 80, lambda: app)
    browser = WSGI_Browser('http://localhost:80/briefkasten/submit')
    browser.app = app
    return browser


def teardown_zopetestbrowser(browser):
    teardown_dropbox(browser.app)


def pytest_funcarg__zbrowser(request):
    return request.cached_setup(
        setup=setup_zopetestbrowser,
        teardown=teardown_zopetestbrowser,
        scope="function",
    )
