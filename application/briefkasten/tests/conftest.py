from pytest import fixture
from briefkasten.dropbox import generate_post_token, generate_drop_id


@fixture
def post_token():
    return generate_post_token(secret=u't0ps3cr3t')


@fixture
def drop_id():
    return generate_drop_id()
