# -*- coding: utf-8 -*-
import pkg_resources
import os
import colander
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import get_renderer
from pyramid.response import FileResponse
from briefkasten import _, is_equal

title = "ZEIT ONLINE Briefkasten"
version = pkg_resources.get_distribution("briefkasten").version


class _FieldStorage(colander.SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (colander.null, None, '', b''):
            return colander.null
        # weak attempt at duck-typing
        if not hasattr(cstruct, 'file'):
            raise colander.Invalid(node, "%s is not a FieldStorage instance" % cstruct)
        return cstruct


class DropboxSchema(colander.MappingSchema):
    message = colander.SchemaNode(
        colander.String(),
        title=_(u'Anonymous submission to the editors'),
        missing=None)
    upload = colander.SchemaNode(
        _FieldStorage(),
        missing=None
    )
    testing_secret = colander.SchemaNode(
        colander.String(),
        missing=u'')


dropbox_schema = DropboxSchema()


def defaults(request):
    return dict(
        static_url=request.static_url('briefkasten:static/'),
        base_url=request.registry.settings.get('appserver_root_url', '/'),
        master=get_renderer('%s:templates/master.pt' % request.registry.settings.get(
            'theme_package', 'briefkasten')).implementation().macros['master'],
        version=version,
        title=title)


def dropbox_form(request):
    """ generates a dropbox uid and renders the submission form with a signed version of that id"""
    from briefkasten import generate_post_token
    token = generate_post_token(secret=request.registry.settings['post_secret'])
    return dict(
        action=request.route_url('dropbox_form_submit', token=token),
        fileupload_url=request.route_url('dropbox_fileupload', token=token),
        **defaults(request))


def dropbox_fileupload(dropbox, request):
    """ accepts a single file upload and adds it to the dropbox as attachment"""
    attachment = request.POST['attachment']
    attached = dropbox.add_attachment(attachment)
    return dict(
        files=[dict(
            name=attached,
            type=attachment.type,
        )]
    )


def dropbox_submission(dropbox, request):
    """ handles the form submission, redirects to the dropbox's status page."""
    try:
        data = dropbox_schema.deserialize(request.POST)
    except Exception:
        return HTTPFound(location=request.route_url('dropbox_form'))

    # set the message
    dropbox.message = data.get('message')

    # recognize submission from watchdog
    if 'testing_secret' in dropbox.settings:
        dropbox.from_watchdog = is_equal(
            dropbox.settings['test_submission_secret'],
            data.pop('testing_secret', ''))

    # a non-js client might have uploaded an attachment via the form's fileupload field:
    if data.get('upload') is not None:
        dropbox.add_attachment(data['upload'])

    # now we can call the process method
    dropbox.submit()
    drop_url = request.route_url('dropbox_view', drop_id=dropbox.drop_id)
    print("Created dropbox %s" % drop_url)
    return HTTPFound(location=drop_url)


def dropbox_submitted(dropbox, request):
    appstruct = defaults(request)
    appstruct.update(
        title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status_code=dropbox.status[0],
        status_int=dropbox.status_int,
        status=dropbox.status,
        replies=dropbox.replies)
    return appstruct


class DropboxReplySchema(colander.MappingSchema):
    reply = colander.SchemaNode(colander.String())
    author = colander.SchemaNode(colander.String())


dropboxreply_schema = DropboxReplySchema()


def dropbox_editor_view(dropbox, request):
    appstruct = defaults(request)
    appstruct.update(
        title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status=dropbox.status,
        replies=dropbox.replies,
        message=None,
        action=request.url,
    )
    return appstruct


def dropbox_reply_submitted(dropbox, request):
    try:
        data = DropboxReplySchema().deserialize(request.POST)
    except Exception:
        appstruct = defaults(request)
        appstruct.update(
            title='%s - %s' % (title, dropbox.status),
            action=request.url,
            message=u'Alle Felder müssen ausgefüllt werden.',
            drop_id=dropbox.drop_id,
        )
        return appstruct
    dropbox.add_reply(data)
    return HTTPFound(location=request.route_url('dropbox_view', drop_id=dropbox.drop_id))


def prometheus_metrics(request):
    """ Serves the static prometheus metrics from the filesystem.
    It is updated each time the janitor runs
    """
    drop_root = request.registry.settings['dropbox_container']
    try:
        return FileResponse(
            os.path.join(drop_root.fs_root, 'metrics'),
            content_type='text/plain')
    except Exception:
        return HTTPNotFound()
