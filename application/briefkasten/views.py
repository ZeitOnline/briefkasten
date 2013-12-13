# -*- coding: utf-8 -*-
import pkg_resources
import colander
import deform
from pyramid.renderers import get_renderer
from pyramid.renderers import render
from pyramid.view import view_config
from briefkasten import dropbox_container, _, is_equal

title = "ZEIT ONLINE Briefkasten"
version = pkg_resources.get_distribution("briefkasten").version


class FileUploadTempStore(dict):
    def preview_url(self, name):
        return ""


tempstore = FileUploadTempStore()
attachments_min_len = 1
attachments_max_len = 10


class Attachments(colander.SequenceSchema):
    attachment = colander.SchemaNode(deform.FileData(),
        missing=None,
        widget=deform.widget.FileUploadWidget(tempstore))


class DropboxSchema(colander.MappingSchema):
    message = colander.SchemaNode(colander.String(),
        title=_(u'Anonymous submission to the editors'),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),)
    attachments = Attachments(title=_(u'Upload files'), missing=None)
    testing_secret = colander.SchemaNode(colander.String(),
        widget=deform.widget.HiddenWidget(), missing=u'')
dropbox_schema = DropboxSchema()


def defaults():
    return dict(master=get_renderer('templates/master.pt').implementation().macros['master'],
        version=version,
        title=title)


@view_config(route_name='dropbox_form',
    request_method='GET',
    renderer='briefkasten:templates/dropbox_submission.pt')
def dropbox_submit(request):
    form = deform.Form(dropbox_schema,
        buttons=[deform.Button('submit', _('Submit'))],
        action=request.url,
        formid='briefkasten-form')
    form['attachments'].widget = deform.widget.SequenceWidget(
        min_len=attachments_min_len,
        max_len=attachments_max_len,
        add_subitem_text_template=_(u'Add another file'))
    appstruct = defaults()
    appstruct.update(drop_id=None,
        form_submitted=False,
        form=form.render())
    return appstruct


@view_config(route_name='dropbox_form',
    request_method='POST',
    renderer='briefkasten:templates/dropbox_submission.pt')
def dropbox_submitted(request):
    appstruct = defaults()
    try:
        data = deform.Form(dropbox_schema,
            formid='briefkasten-form',
            action=request.url,
            buttons=('submit',)).validate(request.POST.items())
        testing_secret = request.registry.settings.get('test_submission_secret', '')
        is_test_submission = is_equal(testing_secret,
            data.pop('testing_secret', ''))
        drop_box = dropbox_container.add_dropbox(**data)
        text = render('briefkasten:templates/editor_email.pt', dict(
            reply_url=request.route_url('dropbox_editor', drop_id=drop_box.drop_id, editor_token=drop_box.editor_token),
            message=drop_box.message,
            num_attachments=drop_box.num_attachments), request)
        drop_box.update_message(text)
        process_status = drop_box.process(testing=is_test_submission)
        try:
            del tempstore[data['attachment']['uid']]
        except (KeyError, TypeError):
            pass
        appstruct.update(form=None,
            form_submitted=True,
            drop_id=drop_box.drop_id,
            process_status=process_status)
    except deform.ValidationFailure, exception:
        appstruct.update(form_submitted=False,
            form=exception.render())
    return appstruct


@view_config(route_name="dropbox_view",
    renderer='briefkasten:templates/feedback.pt')
def dropbox_view(dropbox, request):
    appstruct = defaults()
    appstruct.update(title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status=dropbox.status,
        replies=dropbox.replies)
    return appstruct


class DropboxReplySchema(colander.MappingSchema):
    reply = colander.SchemaNode(colander.String(),
        widget=deform.widget.TextAreaWidget(rows=10, cols=60),)
    author = colander.SchemaNode(colander.String())
dropboxreply_schema = DropboxReplySchema()


@view_config(route_name="dropbox_editor",
    request_method='GET',
    renderer='briefkasten:templates/editor_reply.pt')
def dropbox_editor_view(dropbox, request):
    appstruct = defaults()
    appstruct.update(title='%s - %s' % (title, dropbox.status),
        drop_id=dropbox.drop_id,
        status=dropbox.status,
        replies=dropbox.replies,
        message=None,
        form=deform.Form(dropboxreply_schema, buttons=('submit',)).render())
    return appstruct


@view_config(route_name="dropbox_editor",
    request_method='POST',
    renderer='briefkasten:templates/editor_reply.pt')
def dropbox_reply_submitted(dropbox, request):
    appstruct = defaults()
    try:
        data = deform.Form(dropboxreply_schema,
            buttons=('submit',)).validate(request.POST.items())
        dropbox.add_reply(data)
        appstruct.update(title=u'%s – Reply sent.' % title,
            message=u'Reply sent',
            form=None)
    except deform.ValidationFailure, exception:
        appstruct.update(message=None,
            form=exception.render())
    return appstruct


@view_config(route_name='fingerprint',
    request_method='GET',
    renderer='briefkasten:templates/fingerprint.pt')
def fingerprint(request):
    return defaults()
