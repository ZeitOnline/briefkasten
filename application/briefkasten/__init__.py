# -*- coding: utf-8 -*-
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound

from dropbox import DropboxContainer
dropbox_container = DropboxContainer()

from pyramid.i18n import TranslationStringFactory
_ = TranslationStringFactory('briefkasten')


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
    dropbox = dropbox_factory(request)
    if is_equal(dropbox.editor_token, request.matchdict['editor_token'].encode('utf-8')):
        return dropbox
    else:
        raise HTTPNotFound('invalid editor token')


def german_locale(request):
    return 'de'


def main(global_config, **settings):
    """ Configure and create the main application. """
    config = Configurator(settings=settings, locale_negotiator=german_locale)
    config.add_translation_dirs('briefkasten:locale')
    app_route = settings.get('appserver_root_url', '/')
    config.add_static_view('%sstatic/deform' % app_route, 'deform:static')
    config.add_static_view('%sstatic' % app_route, 'briefkasten:static')
    config.include('pyramid_deform')
    config.add_route('fingerprint', '%sfingerprint' % app_route)
    config.add_route('dropbox_form', '%ssubmit' % app_route)
    config.add_route('dropbox_editor', '%s{drop_id}/{editor_token}' % app_route, factory=dropbox_editor_factory)
    config.add_route('dropbox_view', '%s{drop_id}' % app_route, factory=dropbox_factory)
    config.scan()
    dropbox_container.init(settings)
    return config.make_wsgi_app()
