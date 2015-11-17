# -*- coding: utf-8 -*-
from os.path import dirname, join
from pytest import fixture
from tempfile import mkdtemp
from webtest import TestApp


from briefkasten import main


#
# functional tests with an isolated, temporary dropbox
#
@fixture
def app(request):
    fs_dropbox_root = mkdtemp()
    return main({},
        appserver_root_url='/briefkasten/',
        fs_dropbox_root=fs_dropbox_root,
        fs_bin_path=join(dirname(__file__), 'bin'))


#
# webtest based browser tests
#
# testbrowser based browser tests
#
@fixture
def browser(app, request):
    """ Returns an instance of `webtest.TestApp`.  The `user` pytest marker
        (`pytest.mark.user`) can be used to pre-authenticate the browser
        with the given login name: `@user('admin')`. """
    extra_environ = dict(HTTP_HOST='example.com')
    browser = TestApp(app, extra_environ=extra_environ)
    return browser
