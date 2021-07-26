# -*- coding: utf-8 -*-
from pytest import fixture
from briefkasten import housekeeping


@fixture
def metrics_url(testing):
    return testing.route_url('metrics')


def test_metrics_view_404(browser, metrics_url):
    response = browser.get(metrics_url, status=404)
    assert response.status == '404 Not Found'


def test_metrics_view_200(browser, metrics_url, dropbox_container):
    housekeeping.do(dropbox_container.fs_root)
    response = browser.get(metrics_url)
    assert response.status == '200 OK'
    assert response.content_type == 'text/plain'
