# -*- coding: utf-8 -*-
import colander
import deform
from pyramid.renderers import get_renderer
from pyramid.view import view_config
from briefkasten import dropbox_container, _

title = "ZEIT ONLINE Briefkasten"


class FileUploadTempStore(dict):
    def preview_url(self, name):
        return ""


tempstore = FileUploadTempStore()
attachments_min_len = 3


class Attachments(colander.SequenceSchema):
    attachment = colander.SchemaNode(deform.FileData(),
        missing=None,
        widget=deform.widget.FileUploadWidget(tempstore))


class DropboxSchema(colander.MappingSchema):
    message = colander.SchemaNode(colander.String(),
        title=_(u'Anonymous submission to the editors'),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),)
    attachments = Attachments(title=_(u'Upload files'), missing=None)
dropbox_schema = DropboxSchema()


def get_master():
    return get_renderer('templates/master.pt').implementation().macros['master']


@view_config(route_name='dropbox_form',
    request_method='GET',
    renderer='briefkasten:templates/dropbox_form.pt')
def dropbox_submit(request):
    form = deform.Form(dropbox_schema,
        buttons=[deform.Button('submit', _('Submit'))],
        action=request.url,
        formid='briefkasten-form')
    form['attachments'].widget = deform.widget.SequenceWidget(
        min_len=attachments_min_len,
        max_len=attachments_min_len,
        title=_(u'Add another file'))
    return dict(title=title,
        master=get_master(),
        drop_id=None, form_submitted=False,
        form=form.render())


@view_config(route_name='dropbox_form',
    request_method='POST',
    renderer='briefkasten:templates/dropbox_form.pt')
def dropbox_submitted(request):
    try:
        data = deform.Form(dropbox_schema,
            formid='briefkasten-form',
            action=request.url,
            buttons=('submit',)).validate(request.POST.items())
        drop_box = dropbox_container.add_dropbox(**data)
        process_status = drop_box.process()
        try:
            del tempstore[data['attachment']['uid']]
        except (KeyError, TypeError):
            pass
        return dict(title=title,
            master=get_master(),
            form=None,
            form_submitted=True,
            drop_id=drop_box.drop_id,
            process_status=process_status)
    except deform.ValidationFailure, exception:
        return dict(title=title,
            master=get_master(),
            form_submitted=False,
            form=exception.render())


@view_config(route_name="dropbox_view",
    renderer='briefkasten:templates/dropbox_view.pt')
def dropbox_view(dropbox, request):
    return dict(master=get_master(),
        title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status=dropbox.status,
        replies=dropbox.replies)


class DropboxReplySchema(colander.MappingSchema):
    reply = colander.SchemaNode(colander.String(),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),)
    author = colander.SchemaNode(colander.String())
dropboxreply_schema = DropboxReplySchema()


@view_config(route_name="dropbox_editor",
    request_method='GET',
    renderer='briefkasten:templates/dropbox_reply_form.pt')
def dropbox_editor_view(dropbox, request):
    return dict(master=get_master(),
        title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status=dropbox.status,
        replies=dropbox.replies,
        message=None,
        form=deform.Form(dropboxreply_schema, buttons=('submit',)).render())


@view_config(route_name="dropbox_editor",
    request_method='POST',
    renderer='briefkasten:templates/dropbox_reply_form.pt')
def dropbox_reply_submitted(dropbox, request):
    try:
        data = deform.Form(dropboxreply_schema,
            buttons=('submit',)).validate(request.POST.items())
        dropbox.add_reply(data)
        return dict(master=get_master(),
            title=u'%s – Reply sent.' % title,
            message=u'Reply sent',
            form=None)
    except deform.ValidationFailure, exception:
        return dict(master=get_master(),
            title=title,
            message=None,
            form=exception.render())


@view_config(route_name='fingerprint',
    request_method='GET',
    renderer='briefkasten:templates/fingerprint.pt')
def fingerprint(request):
    master = get_master()
    return dict(master=master,
        title=title)
