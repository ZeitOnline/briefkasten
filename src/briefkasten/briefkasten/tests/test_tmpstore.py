from os.path import exists, join, dirname
from pytest import raises


#
# tempfile store tests
#
def setup_tmpstore():
    from briefkasten.tmpstore import TempFileTempStore
    return TempFileTempStore()


def teardown_tmpstore(tmpstore):
    try:
        tmpstore.destroy()
    except OSError:
        pass


def pytest_funcarg__tmpstore(request):
    return request.cached_setup(
        setup=setup_tmpstore,
        teardown=teardown_tmpstore,
        scope="function"
    )


def _make_one():
    return open(join(dirname(__file__), 'attachment.txt'), 'r')


def test_init_creates_directory(tmpstore):
    assert exists(tmpstore.tempdir)


def test_destroy_deletes_directory(tmpstore):
    tmpstore.destroy()
    assert not exists(tmpstore.tempdir)


def test_preview_url(tmpstore):
    assert tmpstore.preview_url('foo') is None


def test_not_in(tmpstore):
    assert 'foobar' not in tmpstore


def test_setting(tmpstore):
    tmpstore['foo'] = dict(fp=_make_one(), mime_type='text/plain')
    assert 'foo' in tmpstore
    # make sure the temporary files have been created:
    assert exists(join(tmpstore.tempdir, 'foo'))
    assert exists(join(tmpstore.tempdir, 'foo.json'))


def test_getting(tmpstore):
    tmpstore['foo'] = dict(fp=_make_one(), mime_type='text/plain')
    entry = tmpstore['foo']
    assert entry['mime_type'] == 'text/plain'
    assert 'Schönen Guten Tag!' in entry['fp'].read().encode('utf-8')


def test_getting_non_existent(tmpstore):
    with raises(KeyError):
        tmpstore['bar']


def test_dict_get_successful(tmpstore):
    tmpstore['foo'] = dict(fp=_make_one(), mime_type='text/plain')
    entry = tmpstore.get('foo')
    assert entry['mime_type'] == 'text/plain'


def test_dict_get_failed(tmpstore):
    entry = tmpstore.get('foo', 'bar')
    assert entry == 'bar'


def test_delete_non_existent(tmpstore):
    with raises(KeyError):
        del tmpstore['bar']


def test_successful_delete(tmpstore):
    tmpstore['foo'] = dict(fp=_make_one(), mime_type='text/plain')
    assert 'foo' in tmpstore
    del tmpstore['foo']
    assert 'foo' not in tmpstore
    # make sure the temporary files have been deleted:
    assert not exists(join(tmpstore.tempdir, 'foo'))
    assert not exists(join(tmpstore.tempdir, 'foo.json'))
