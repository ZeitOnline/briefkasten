# -*- coding: utf-8 -*-
import gnupg
import shutil
import tarfile
from cStringIO import StringIO as BIO
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer
from json import load, dumps
from os import mkdir, chmod, listdir, environ
from os.path import exists, isfile, join, splitext, basename
from subprocess import call
from pyramid.settings import asbool, aslist
from random import SystemRandom


allchars = '23456qwertasdfgzxcvbQWERTASDFGZXCVB789yuiophjknmYUIPHJKLNM'


def generate_drop_id(length=8):
    rng = SystemRandom()
    drop_id = ""
    for i in range(length):
        drop_id += rng.choice(allchars)
    return drop_id


def generate_post_token(secret):
    """ returns a URL safe, signed token that contains a UUID"""
    return URLSafeTimedSerializer(secret, salt=u'post').dumps(generate_drop_id())


def parse_post_token(token, secret, max_age=300):
    return URLSafeTimedSerializer(secret, salt=u'post').loads(token, max_age=max_age)


def sanitize_filename(filename):
    """preserve the file ending, but replace the name with a random token """
    # TODO: fix broken splitext (it reveals everything of the filename after the first `.` - doh!)
    token = generate_drop_id()
    name, extension = splitext(filename)
    if extension:
        return '%s%s' % (token, extension)
    else:
        return token


class DropboxContainer(object):

    settings = None

    def __init__(self, settings=None):
        if settings is not None:
            self.init(settings)

    def init(self, settings):
        self.settings = settings
        self.fs_path = settings['fs_dropbox_root']
        from os import makedirs
        if not exists(self.fs_path):
            makedirs(self.fs_path)

    def add_dropbox(self, drop_id, message=None, attachments=None):
        return Dropbox(self, drop_id, message=message, attachments=attachments)

    def get_dropbox(self, drop_id):
        """ returns the dropbox with the given id, if it does not exist an empty dropbox
        will be created and returned"""
        return Dropbox(self, drop_id=drop_id)

    def destroy(self):
        shutil.rmtree(self.fs_path)

    def __contains__(self, drop_id):
        return exists(join(self.fs_path, drop_id))


def checkRecipient(gpg_context, r):
    uid = '<' + r + '>'
    valid_keys = [k for k in gpg_context.list_keys() if uid in ', '.join(k['uids']) and k['trust'] in 'ofqmu-']
    return bool(valid_keys)


def sendMultiPart(smtp, gpg_context, sender, recipients, subject, text, attachments):
    """ a helper method that composes and sends an email with attachments
    requires a pre-configured smtplib.SMTP instance"""
    sent = 0
    for to in recipients:
        if not checkRecipient(gpg_context, to):
            continue

        msg = MIMEMultipart()

        msg['From'] = sender
        msg['To'] = to
        msg['Subject'] = subject
        msg.preamble = u'This is an email in encrypted multipart format.'

        with open(text, 'r') as text_message:
            attach = MIMEText(str(gpg_context.encrypt_file(text_message, to, always_trust=True)))
            attach.set_charset('UTF-8')
            msg.attach(attach)

        for attachment in attachments:
            with open(attachment, 'rb') as fp:
                attach = MIMEBase('application', 'octet-stream')
                attach.set_payload(str(gpg_context.encrypt_file(fp, to, always_trust=True)))
            attach.add_header('Content-Disposition', 'attachment', filename=basename('%s.pgp' % attachment))
            msg.attach(attach)

        # TODO: need to catch exception?
        smtp.begin()
        smtp.sendmail(sender, to, msg.as_string())
        smtp.quit()
        sent += 1

    return sent


class Dropbox(object):

    def __init__(self, container, drop_id, message=None, attachments=None):
        """
        the attachments are expected to conform to what the webob library uses for file uploads,
        namely an instance of `cgi.FieldStorage` with the following attributes:
            - a file handle under the key `file`
            - the name of the file under `filename`
        """
        self.drop_id = drop_id
        self.container = container
        self.paths_created = []
        self.fs_path = fs_dropbox_path = join(container.fs_path, drop_id)

        if not exists(fs_dropbox_path):
            mkdir(fs_dropbox_path)
            chmod(fs_dropbox_path, 0770)
            self.paths_created.append(fs_dropbox_path)
            self.status = u'010 created'
            # create an editor token
            self.editor_token = editor_token = generate_drop_id()
            self._write_message(fs_dropbox_path, 'editor_token', editor_token)
        else:
            self.editor_token = open(join(self.fs_path, 'editor_token')).readline()

        if message is not None:
            # write the message into a file
            self._write_message(fs_dropbox_path, 'message', message)
            self.message = message

        # write the attachment into a file
        if attachments is not None:
            for attachment in attachments:
                if attachment is None:
                    continue
                self.add_attachment(attachment)
        self.fs_replies_path = join(self.fs_path, 'replies')

    @property
    def settings(self):
        return self.container.settings

    @property
    def fs_attachment_container(self):
        return join(self.fs_path, 'attach')

    def update_message(self, newtext):
        """ overwrite the message text. this also updates the corresponding file. """
        self._write_message(self.fs_path, 'message', newtext)

    def add_attachment(self, attachment):
        fs_attachment_container = self.fs_attachment_container
        if not exists(fs_attachment_container):
            mkdir(fs_attachment_container)
            chmod(fs_attachment_container, 0770)
            self.paths_created.append(fs_attachment_container)
        sanitized = sanitize_filename(attachment.filename)
        fs_attachment_path = join(fs_attachment_container, sanitized)
        with open(fs_attachment_path, 'w') as fs_attachment:
            shutil.copyfileobj(attachment.file, fs_attachment)
        fs_attachment.close()
        chmod(fs_attachment_path, 0660)
        self.paths_created.append(fs_attachment_path)
        return sanitized

    def process(self, purge_meta_data=True, testing=False):
        """ Calls the external cleanser scripts to (optionally) purge the meta data and then
            send the contents of the dropbox via email.
        """
        self.status = u'020 submitted'
        gpg_context = gnupg.GPG(gnupghome=self.settings['fs_pgp_pubkeys'])
        editors = aslist(self.settings['editors'])
        admins = aslist(self.settings['admins'])

        # create initial backup if we can't clean
        backup_recipients = [r for r in editors + admins if checkRecipient(gpg_context, r)]

        # this will be handled by watchdog, no need to send for each drop
        if not backup_recipients:
            self.status = u'500 no valid keys at all'
            return self.status

        self.status = u'100 processor running'

        if asbool(self.settings.get('debug', False)):  # use bool helper
            file_out = BIO()
            with tarfile.open(mode='w|', fileobj=file_out) as tar:
                tar.add(join(self.fs_path, 'message'))
                if exists(join(self.fs_path, 'attach')):
                    tar.add(join(self.fs_path, 'attach'))
            gpg_context.encrypt(
                file_out.getvalue(),
                backup_recipients,
                always_trust=True,
                output=join(self.fs_path, 'backup.tar.gpg')
            )

        if self.num_attachments > 0:
            fs_process = join(self.settings['fs_bin_path'], 'process-attachments.sh')
            fs_config = join(self.settings['fs_bin_path'],
                'briefkasten%s.conf' % ('_test' if testing else ''))
            shellenv = environ.copy()
            shellenv['PATH'] = '%s:%s:/usr/local/bin/:/usr/local/sbin/' % (shellenv['PATH'], self.settings['fs_bin_path'])
            call("%s -d %s -c %s" % (fs_process, self.fs_path, fs_config), shell=True,
                env=shellenv)

        attachments_cleaned = []
        cleaned = join(self.fs_path, 'clean')
        if exists(cleaned):
            attachments_cleaned = [join(cleaned, f) for f in listdir(cleaned) if isfile(join(cleaned, f))]

        sendMultiPart(
            self.settings['smtp'],
            gpg_context,
            self.settings['mail.default_sender'],
            editors,
            u'Drop %s' % self.drop_id,
            join(self.fs_path, 'message'),
            attachments_cleaned
        )
        self.status = '090 success'
        return self.status

    def add_reply(self, reply):
        """ Add an editorial reply to the drop box.

            :param reply: the message, must conform to  :class:`views.DropboxReplySchema`

        """
        self._write_message(self.fs_replies_path, 'message_001.txt', dumps(reply))

    def _write_message(self, fs_container, fs_name, message):
        if not exists(fs_container):
            mkdir(fs_container)
            chmod(fs_container, 0770)
        fs_reply_path = join(fs_container, fs_name)
        with open(fs_reply_path, 'w') as fs_reply:
            fs_reply.write(message.encode('utf-8'))
        chmod(fs_reply_path, 0660)
        self.paths_created.append(fs_reply_path)

    @property
    def num_attachments(self):
        """returns the current number of uploaded attachments in the filesystem"""
        if exists(self.fs_attachment_container):
            return len(listdir(self.fs_attachment_container))
        else:
            return 0

    @property
    def replies(self):
        """ returns a list of strings """
        fs_reply_path = join(self.fs_replies_path, 'message_001.txt')
        if exists(fs_reply_path):
            return [load(open(fs_reply_path, 'r'))]
        else:
            return []

    @property
    def status(self):
        """ returns either 'created', 'quarantined', 'success' or 'failure'
        """
        try:
            with open(join(self.fs_path, u'status')) as status_file:
                return status_file.readline()
        except IOError:
            return u'000 no status file'

    @property
    def status_int(self):
        """ returns the status as integer, so it can be used in comparisons"""
        return int(self.status.split()[0])

    @status.setter
    def status(self, state):
        with open(join(self.fs_path, u'status'), 'w') as status_file:
            status_file.write(state)
        if self.status_int >= 500:
            self.wipe()

    def sanitize(self):
        """ removes all unencrypted user input """

    def wipe(self):
        """ removes all data except the status file"""
        # TODO: erdgeist :)
        pass
