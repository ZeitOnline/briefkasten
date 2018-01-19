from py.test import fixture

size_values = {
    '200': 200,
    '20M': 20000000,
    '1Gb': 1000000000
}


@fixture(params=size_values.items())
def sizes(request, tmpdir):
    return request.param


def test_attachment_size_threshold_humanfriendly(sizes, tmpdir):
    human_size, byte_size = sizes
    from briefkasten.dropbox import DropboxContainer
    dropbox_container = DropboxContainer(
        root=tmpdir.strpath,
        settings=dict(
            attachment_size_threshold=human_size,
            fs_pgp_pubkeys=None)
    )
    assert (dropbox_container.settings['attachment_size_threshold'] == byte_size)
