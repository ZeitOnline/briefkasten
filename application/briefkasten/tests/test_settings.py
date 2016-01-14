from py.test import fixture

sizes = {
    '200': 200,
    '20M': 20971520,
    '1Gb': 1073741824
}


@fixture(params=sizes.keys())
def settings(request, settings):
    return dict(settings, attachment_size_threshold=request.param)


def test_attachment_size_threshold_humanfriendly(app, settings):
    assert app.registry.settings['attachment_size_threshold'] == sizes[settings['attachment_size_threshold']]
