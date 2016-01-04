# -*- coding: utf-8 -*-
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound, HTTPGone
from pyramid.i18n import TranslationStringFactory
from itsdangerous import SignatureExpired
from dropbox import DropboxContainer

dropbox_container = DropboxContainer()
_ = TranslationStringFactory('briefkasten')


def dropbox_post_factory(request):
    from .dropbox import parse_post_token
    try:
        drop_id = parse_post_token(
            token=request.matchdict['token'],
            secret=request.registry.settings['post_secret'])
    except SignatureExpired:
        raise HTTPGone('dropbox expired')
    except Exception:  # don't be too specific on the reason for the error
        raise HTTPNotFound('no such dropbox')
    return dropbox_container.get_dropbox(drop_id)


def dropbox_factory(request):
    try:
        return dropbox_container.get_dropbox(request.matchdict['drop_id'])
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


def main(global_config, **settings):
    """ Configure and create the main application. """
    config = Configurator(settings=settings, locale_negotiator=german_locale)
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
    config.scan()
    dropbox_container.init(settings)
    return config.make_wsgi_app()
