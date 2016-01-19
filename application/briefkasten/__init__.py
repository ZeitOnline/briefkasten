# -*- coding: utf-8 -*-
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound, HTTPGone
from pyramid.i18n import TranslationStringFactory
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from .dropbox import DropboxContainer, generate_drop_id

_ = TranslationStringFactory('briefkasten')


def generate_post_token(secret):
    """ returns a URL safe, signed token that contains a UUID"""
    return URLSafeTimedSerializer(secret, salt=u'post').dumps(generate_drop_id())


def parse_post_token(token, secret, max_age=300):
    return URLSafeTimedSerializer(secret, salt=u'post').loads(token, max_age=max_age)


def dropbox_post_factory(request):
    """receives a UUID via the request and returns either a fresh or an existing dropbox
    for it"""
    try:
        drop_id = parse_post_token(
            token=request.matchdict['token'],
            secret=request.registry.settings['post_secret'])
    except SignatureExpired:
        raise HTTPGone('dropbox expired')
    except Exception:  # don't be too specific on the reason for the error
        raise HTTPNotFound('no such dropbox')
    dropbox = request.registry.settings['dropbox_container'].get_dropbox(drop_id)
    if dropbox.status_int >= 20:
        raise HTTPGone('dropbox already in processing, no longer accepts data')
    return dropbox


def dropbox_factory(request):
    """ expects the id of an existing dropbox and returns its instance"""
    try:
        return request.registry.settings['dropbox_container'].get_dropbox(request.matchdict['drop_id'])
    except KeyError:
        raise HTTPNotFound('no such dropbox')


def is_equal(a, b):
    """ a constant time comparison implementation taken from
        http://codahale.com/a-lesson-in-timing-attacks/ and
        Django's `util` module https://github.com/django/django/blob/master/django/utils/crypto.py#L82
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def dropbox_editor_factory(request):
    """ this factory also requires the editor token"""
    dropbox = dropbox_factory(request)
    if is_equal(dropbox.editor_token, request.matchdict['editor_token'].encode('utf-8')):
        return dropbox
    else:
        raise HTTPNotFound('invalid editor token')


def german_locale(request):
    """ a 'negotiator' that always returns german"""
    return 'de'


def configure(global_config, **settings):
    config = Configurator(settings=settings, locale_negotiator=german_locale)
    config.begin()
    config.add_translation_dirs('briefkasten:locale')
    app_route = settings.get('appserver_root_url', '/')
    config.add_static_view('%sstatic' % app_route, 'briefkasten:static')
    config.add_renderer('.pt', 'pyramid_chameleon.zpt.renderer_factory')
    config.add_route('fingerprint', '%sfingerprint' % app_route)
    config.add_route('dropbox_form_submit', '%s{token}/submit' % app_route, factory=dropbox_post_factory)
    config.add_route('dropbox_fileupload', '%s{token}/upload' % app_route, factory=dropbox_post_factory)
    config.add_route('dropbox_editor', '%sdropbox/{drop_id}/{editor_token}' % app_route, factory=dropbox_editor_factory)
    config.add_route('dropbox_view', '%sdropbox/{drop_id}' % app_route, factory=dropbox_factory)
    config.add_route('dropbox_form', app_route)
    config.scan(ignore=['.testing'])
    config.registry.settings['dropbox_container'] = DropboxContainer(root=config.registry.settings['fs_dropbox_root'])
    config.commit()
    return config


def main(global_config, **settings):
    """ Configure and create the main application. """
    return configure(global_config, **settings).make_wsgi_app()
