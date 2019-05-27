# -*- coding: utf-8 -*-
import pkg_resources
import colander
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import get_renderer
from pyramid.view import view_config
from briefkasten import _, is_equal

title = "ZEIT ONLINE Briefkasten"
version = pkg_resources.get_distribution("briefkasten").version


class _FieldStorage(colander.SchemaType):
    def deserialize(self, node, cstruct):
        if cstruct in (colander.null, None, ''):
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
        master=get_renderer('templates/master.pt').implementation().macros['master'],
        version=version,
        title=title)


@view_config(
    route_name='dropbox_form',
    request_method='GET',
    renderer='briefkasten:templates/dropbox_form.pt')
def dropbox_form(request):
    """ generates a dropbox uid and renders the submission form with a signed version of that id"""
    from briefkasten import generate_post_token
    token = generate_post_token(secret=request.registry.settings['post_secret'])
    return dict(
        action=request.route_url('dropbox_form_submit', token=token),
        fileupload_url=request.route_url('dropbox_fileupload', token=token),
        form=request.registry.settings.get(u'briefkasten_flavour', u'briefkasten'),
        editors=request.registry.settings['dropbox_container'].settings.get('editors', []),
        **defaults(request))


@view_config(
    route_name='dropbox_fileupload',
    accept='application/json',
    renderer='json',
    request_method='POST')
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


@view_config(
    route_name='dropbox_form_submit',
    request_method='POST')
def dropbox_submission(dropbox, request):
    """ handles the form submission, redirects to the dropbox's status page."""
    try:
        data = dropbox_schema.deserialize(request.POST)
    except Exception:
        return HTTPFound(location=request.route_url('dropbox_form'))

    recipients = request.POST.getall('recipients')
    if recipients:
        dropbox.set_editors(recipients)

    if not request.POST.get('want_feedback', ''):
        dropbox.disable_feedback()

    # set the message
    dropbox.message = data.get('message')

    # recognize submission from watchdog
    if 'testing_secret' in dropbox.settings:
        dropbox.from_watchdog = is_equal(
            unicode(dropbox.settings['test_submission_secret']),
            data.pop('testing_secret', u''))

    # a non-js client might have uploaded an attachment via the form's fileupload field:
    if data.get('upload') is not None:
        dropbox.add_attachment(data['upload'])

    # now we can call the process method
    dropbox.submit()
    drop_url = request.route_url('dropbox_view', drop_id=dropbox.drop_id)
    print("Created dropbox %s" % drop_url)
    return HTTPFound(location=drop_url)


@view_config(
    route_name="dropbox_view",
    renderer='briefkasten:templates/feedback.pt')
def dropbox_submitted(dropbox, request):
    appstruct = defaults(request)
    appstruct.update(
        title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status_code=dropbox.status[0],
        status_int=dropbox.status_int,
        status=dropbox.status,
        want_feedback=dropbox.want_feedback,
        replies=dropbox.replies)
    return appstruct


class DropboxReplySchema(colander.MappingSchema):
    reply = colander.SchemaNode(colander.String())
    author = colander.SchemaNode(colander.String())
dropboxreply_schema = DropboxReplySchema()


@view_config(
    route_name="dropbox_editor",
    request_method='GET',
    renderer='briefkasten:templates/editor_reply.pt')
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


@view_config(
    route_name="dropbox_editor",
    request_method='POST',
    renderer='briefkasten:templates/editor_reply.pt')
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
