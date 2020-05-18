# -*- coding: utf-8 -*-
import gnupg
import shutil
import yaml
from humanfriendly import parse_size
from jinja2 import Environment, PackageLoader
from json import load, dumps
from os import makedirs, mkdir, chmod, environ, listdir, remove, stat
from os.path import exists, isdir, join, splitext, getmtime, split
from datetime import datetime
from random import SystemRandom
from zipfile import ZipFile, ZIP_STORED
from subprocess import call

from .notifications import (
    checkRecipient,
    sendMultiPart,
    setup_smtp_factory
)

allchars = '23456qwertasdfgzxcvbQWERTASDFGZXCVB789yuiophjknmYUIPHJKLNM'


def generate_drop_id(length=8):
    rng = SystemRandom()
    drop_id = ""
    for i in range(length):
        drop_id += rng.choice(allchars)
    return drop_id


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

    def __init__(self, root=None, settings=None):
        self.fs_root = root
        self.fs_path = join(root, 'drops')
        self.fs_submission_queue = join(root, 'submissions')
        self.fs_scratch = join(root, 'scratch')

        # initialise settings from disk and parameters
        # settings provided as init parameter take precedence over values on-disk
        # which in turn take precedence over default values
        self.settings = dict(
            attachment_size_threshold=u'2Mb',
        )

        self.settings.update(**self.parse_settings())
        if settings is not None:
            self.settings.update(**settings)

        # set archive paths
        self.fs_archive_cleansed = self.settings.get('dropbox_cleansed_archive_path', join(root, 'archive_cleansed'))
        self.fs_archive_dirty = self.settings.get('dropbox_dirty_archive_path', join(root, 'archive_dirty'))
        self.fs_archive = dict(
            clean=self.fs_archive_cleansed,
            dirty=self.fs_archive_dirty,
        )

        # set smtp instance defensively, to not overwrite mocked version from test settings:
        if 'smtp' not in self.settings:
            self.settings['smtp'] = setup_smtp_factory(**self.settings)

        # setup GPG
        self.gpg_context = gnupg.GPG(
            gnupghome=self.settings['fs_pgp_pubkeys'],
            gpgbinary=self.settings.get('fs_gpg_path', 'gpg'),
        )

        # convert human readable size to bytes
        self.settings['attachment_size_threshold'] = parse_size(self.settings['attachment_size_threshold'])

        # ensure directories exist
        for directory in [
                self.fs_root,
                self.fs_path,
                self.fs_submission_queue,
                self.fs_archive_cleansed,
                self.fs_archive_dirty,
                self.fs_scratch]:
            if not exists(directory):
                makedirs(directory)

    def parse_settings(self):
        fs_settings = join(self.fs_root, 'settings.yaml')
        if exists(fs_settings):
            with open(fs_settings, 'r') as settings:
                return yaml.load(settings, Loader=yaml.FullLoader)
        else:
            return dict()

    def add_dropbox(self, drop_id, message=None, attachments=None, from_watchdog=False):
        return Dropbox(self, drop_id, message=message, attachments=attachments, from_watchdog=from_watchdog)

    def get_dropbox(self, drop_id):
        """ returns the dropbox with the given id, if it does not exist an empty dropbox
        will be created and returned"""
        return Dropbox(self, drop_id=drop_id)

    def destroy(self):
        shutil.rmtree(self.fs_root)

    def __contains__(self, drop_id):
        return exists(join(self.fs_path, drop_id))

    def __iter__(self):
        for candidate in listdir(self.fs_path):
            if isdir(join(self.fs_path, candidate)):
                yield self.get_dropbox(candidate)


class Dropbox(object):

    def __init__(self, container, drop_id, message=None, attachments=None, from_watchdog=False):
        """
        the attachments are expected to conform to what the webob library uses for file uploads,
        namely an instance of `cgi.FieldStorage` with the following attributes:
            - a file handle under the key `file`
            - the name of the file under `filename`
        """
        self.drop_id = drop_id
        self.container = container
        self.paths_created = []
        self.send_attachments = False
        self.fs_path = fs_dropbox_path = join(container.fs_path, drop_id)
        self.fs_attachment_container = join(self.fs_path, 'attach')
        self.fs_cleansed_attachment_container = join(self.fs_path, 'clean')
        self.fs_replies_path = join(self.fs_path, 'replies')
        self.gpg_context = self.container.gpg_context
        self.admins = self.settings['admins']
        self.editors = self.settings['editors']
        self.theme_package = self.settings.get('theme_package', 'briefkasten')
        self.jinja_env = Environment(loader=PackageLoader(self.theme_package, 'templates'))

        if not exists(fs_dropbox_path):
            mkdir(fs_dropbox_path)
            chmod(fs_dropbox_path, 0o770)
            self.paths_created.append(fs_dropbox_path)
            self.status = u'010 created'
            # create an editor token
            self.editor_token = editor_token = generate_drop_id()
            self._write_message(fs_dropbox_path, 'editor_token', editor_token)
            self.from_watchdog = from_watchdog
        else:
            self.editor_token = open(join(self.fs_path, 'editor_token')).readline()

        # set recipients of email depending on watchdog status
        if self.from_watchdog:
            self.editors = [self.settings['watchdog_imap_recipient']]
        else:
            self.editors = self.settings['editors']

        if message is not None:
            # write the message into a file
            self._write_message(fs_dropbox_path, 'message', message)

        # write the attachment into a file
        if attachments is not None:
            for attachment in attachments:
                if attachment is None:
                    continue
                self.add_attachment(attachment)

    #
    # top level methods that govern the life cycle of a dropbox:

    def add_attachment(self, attachment):
        fs_attachment_container = self.fs_attachment_container
        if not exists(fs_attachment_container):
            mkdir(fs_attachment_container)
            chmod(fs_attachment_container, 0o770)
            self.paths_created.append(fs_attachment_container)
        sanitized_filename = sanitize_filename(attachment.filename)
        fs_attachment_path = join(fs_attachment_container, sanitized_filename)
        with open(fs_attachment_path, 'wb') as fs_attachment:
            shutil.copyfileobj(attachment.file, fs_attachment)
        fs_attachment.close()
        chmod(fs_attachment_path, 0o660)
        self.paths_created.append(fs_attachment_path)
        return sanitized_filename

    def submit(self):
        with open(join(self.container.fs_submission_queue, self.drop_id), 'w'):
            pass
        self.status = u'020 submitted'

    def process(self):
        """ Calls the external cleanser scripts to (optionally) purge the meta data and then
            send the contents of the dropbox via email.
        """

        if self.num_attachments > 0:
            self.status = u'100 processor running'
            fs_dirty_archive = self._create_backup()
            # calling _process_attachments has the side-effect of updating `send_attachments`
            self._process_attachments()
            if self.status_int < 500 and not self.send_attachments:
                    self._create_archive()

        if self.status_int >= 500 and self.status_int < 600:
            # cleansing failed
            # if configured, we need to move the uncleansed archive to
            # the appropriate folder and notify the editors
            if 'dropbox_dirty_archive_url_format' in self.settings:
                # create_archive
                shutil.move(
                    fs_dirty_archive,
                    '%s/%s.zip.pgp' % (self.container.fs_archive_dirty, self.drop_id))
                # update status
                # it's now considered 'successful-ish' again
                self.status = '490 cleanser failure but notify success'

        if self.status_int == 800:
            # at least one attachment was not supported
            # if configured, we need to move the uncleansed archive to
            # the appropriate folder and notify the editors
            if 'dropbox_dirty_archive_url_format' in self.settings:
                # create_archive
                shutil.move(
                    fs_dirty_archive,
                    '%s/%s.zip.pgp' % (self.container.fs_archive_dirty, self.drop_id))

        if self.status_int < 500 or self.status_int == 800:
            try:
                if self._notify_editors() > 0:
                    if self.status_int < 500:
                        self.status = '900 success'
                else:
                    self.status = '605 smtp failure'
            except Exception:
                import traceback
                tb = traceback.format_exc()
                self.status = '610 smtp error (%s)' % tb

        self.cleanup()
        return self.status

    def cleanup(self):
        """ ensures that no data leaks from drop after processing by
        removing all data except the status file"""
        try:
            remove(join(self.fs_path, u'message'))
            remove(join(self.fs_path, 'dirty.zip.pgp'))
        except OSError:
            pass
        shutil.rmtree(join(self.fs_path, u'clean'), ignore_errors=True)
        shutil.rmtree(join(self.fs_path, u'attach'), ignore_errors=True)

    def add_reply(self, reply):
        """ Add an editorial reply to the drop box.

            :param reply: the message, must conform to  :class:`views.DropboxReplySchema`

        """
        self._write_message(self.fs_replies_path, 'message_001.txt', dumps(reply))

    #
    # "private" helper methods for processing a drop

    def _create_encrypted_zip(self, source='dirty', fs_target_dir=None):
        """ creates a zip file from the drop and encrypts it to the editors.
        the encrypted archive is created inside fs_target_dir"""
        backup_recipients = [r for r in self.editors if checkRecipient(self.gpg_context, r)]

        # this will be handled by watchdog, no need to send for each drop
        if not backup_recipients:
            self.status = u'500 no valid keys at all'
            return self.status

        # calculate paths
        fs_backup = join(self.fs_path, '%s.zip' % source)
        if fs_target_dir is None:
            fs_backup_pgp = join(self.fs_path, '%s.zip.pgp' % source)
        else:
            fs_backup_pgp = join(fs_target_dir, '%s.zip.pgp' % self.drop_id)
        fs_source = dict(
            dirty=self.fs_dirty_attachments,
            clean=self.fs_cleansed_attachments
        )

        # create archive
        with ZipFile(fs_backup, 'w', ZIP_STORED) as backup:
            if exists(join(self.fs_path, 'message')):
                backup.write(join(self.fs_path, 'message'), arcname='message')
            for fs_attachment in fs_source[source]:
                backup.write(fs_attachment, arcname=split(fs_attachment)[-1])

        # encrypt archive
        with open(fs_backup, "rb") as backup:
            self.gpg_context.encrypt_file(
                backup,
                backup_recipients,
                always_trust=True,
                output=fs_backup_pgp
            )

        # cleanup
        remove(fs_backup)
        return fs_backup_pgp

    def _create_backup(self):
        self.status = u'101 creating initial encrypted backup'
        return self._create_encrypted_zip(source='dirty')

    def _process_attachments(self):
        self.status = u'105 processing attachments'
        fs_process = join(self.settings['fs_bin_path'], 'process-attachments.sh')
        fs_config = join(self.settings['fs_bin_path'], 'briefkasten.conf')
        shellenv = environ.copy()
        shellenv['PATH'] = '%s:%s:/usr/local/bin/:/usr/local/sbin/' % (shellenv['PATH'], self.settings['fs_bin_path'])
        call(
            "%s -d %s -c %s" % (fs_process, self.fs_path, fs_config),
            shell=True,
            env=shellenv)
        # status is now < 500 if cleansing was successful or >= 500 && < 600 if cleansing failed
        # or 800 if cleansing was not supported
        # update the decision whether to include attachments in email or not based on size of cleansed attachments:
        # and whether we have an archive for uncleansed attachemts (if we do, don't send them via email, if we
        # don't do send them via email, because otherwise editors would never receive those at all.)
        if self.status_int < 500:
            self.send_attachments = self.size_attachments < self.settings.get('attachment_size_threshold', 0)
        elif self.status_int == 800 and 'dropbox_dirty_archive_url_format' not in self.settings:
            self.send_attachments = True
        else:
            self.send_attachments = False

    def _create_archive(self):
        """ creates an encrypted archive of the dropbox outside of the drop directory.
        """
        self.status = u'270 creating final encrypted backup of cleansed attachments'
        return self._create_encrypted_zip(source='clean', fs_target_dir=self.container.fs_archive_cleansed)

    def _notify_editors(self):
        if self.send_attachments:
            attachments = self.fs_cleansed_attachments
        else:
            attachments = []
        return sendMultiPart(
            self.settings['smtp'],
            self.gpg_context,
            self.settings['mail.default_sender'],
            self.editors,
            u'Drop %s' % self.drop_id,
            self._notification_text,
            attachments
        )

    #
    # helper properties:

    @property
    def num_attachments(self):
        """returns the current number of uploaded attachments in the filesystem"""
        if exists(self.fs_attachment_container):
            return len(listdir(self.fs_attachment_container))
        else:
            return 0

    @property
    def size_attachments(self):
        """returns the number of bytes that the cleansed attachments take up on disk"""
        total_size = 0
        for attachment in self.fs_cleansed_attachments:
                total_size += stat(attachment).st_size
        return total_size

    @property
    def replies(self):
        """ returns a list of strings """
        fs_reply_path = join(self.fs_replies_path, 'message_001.txt')
        if exists(fs_reply_path):
            return [load(open(fs_reply_path, 'r'))]
        else:
            return []

    @property
    def message(self):
        """ returns the user submitted text
        """
        try:
            with open(join(self.fs_path, u'message')) as message_file:
                return u''.join([line for line in message_file.readlines()])
        except IOError:
            return ''

    @message.setter
    def message(self, newtext):
        """ overwrite the message text. this also updates the corresponding file. """
        self._write_message(self.fs_path, 'message', newtext)

    @property
    def from_watchdog(self):
        try:
            with open(join(self.fs_path, u'from_watchdog')):
                return True
        except IOError:
            return False

    @from_watchdog.setter
    def from_watchdog(self, value):
        fs_path = join(self.fs_path, u'from_watchdog')
        if value:
            with open(fs_path, 'w') as status_file:
                status_file.write('True')
        else:
            if exists(fs_path):
                remove(fs_path)

    @property
    def status(self):
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

    def _write_message(self, fs_container, fs_name, message):
        if message is None:
            return
        if not exists(fs_container):
            mkdir(fs_container)
            chmod(fs_container, 0o770)
        fs_reply_path = join(fs_container, fs_name)
        with open(fs_reply_path, 'w') as fs_reply:
            fs_reply.write(message)
        chmod(fs_reply_path, 0o660)
        self.paths_created.append(fs_reply_path)

    @property
    def _notification_text(self):
        return self.jinja_env.get_template('editor_email.j2').render(
            num_attachments=self.num_attachments,
            dropbox=self)

    @property
    def settings(self):
        return self.container.settings

    @property
    def fs_dirty_attachments(self):
        """ returns a list of absolute paths to the attachements"""
        if exists(self.fs_attachment_container):
            return [join(self.fs_attachment_container, attachment)
                    for attachment in listdir(self.fs_attachment_container)]
        else:
            return []

    @property
    def fs_cleansed_attachments(self):
        """ returns a list of absolute paths to the cleansed attachements"""
        if exists(self.fs_cleansed_attachment_container):
            return [join(self.fs_cleansed_attachment_container, attachment)
                    for attachment in listdir(self.fs_cleansed_attachment_container)]
        else:
            return []

    @property
    def cleansed_archive_url(self):
        if 'dropbox_cleansed_archive_url_format' in self.settings:
            return self.settings['dropbox_cleansed_archive_url_format'] % self.drop_id

    @property
    def dirty_archive_url(self):
        if 'dropbox_dirty_archive_url_format' in self.settings:
            return self.settings['dropbox_dirty_archive_url_format'] % self.drop_id

    @property
    def drop_url(self):
        return self.settings['dropbox_view_url_format'] % self.drop_id

    @property
    def editor_url(self):
        return self.settings['dropbox_editor_url_format'] % (
            self.drop_id,
            self.editor_token)

    def last_changed(self):
        # TODO: maybe use last reply from editor
        if exists(join(self.fs_path, u'status')):
            mtime = getmtime(join(self.fs_path, u'status'))
            return datetime.utcfromtimestamp(mtime)
        return datetime.utcfromtimestamp(0)

    def destroy(self):
        shutil.rmtree(self.fs_path)

    def __repr__(self):
        return u'Dropbox %s (%s) at %s' % (
            self.drop_id,
            self.status,
            self.fs_path,
        )
