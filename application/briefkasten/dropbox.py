# -*- coding: utf-8 -*-
import shutil
from itsdangerous import URLSafeTimedSerializer
from json import load, dumps
from os import mkdir, chmod, environ, listdir
from os.path import exists, join, splitext
from random import SystemRandom
from subprocess import call, Popen


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
        return Dropbox(self, drop_id=drop_id)

    def destroy(self):
        shutil.rmtree(self.fs_path)

    def __contains__(self, drop_id):
        return exists(join(self.fs_path, drop_id))


class Dropbox(object):

    def __init__(self, container, drop_id, message=None, attachments=None):
        """
        the attachments are expected to conform to what the deform library serializes for a file widget,
        namely a dictionary containing:
            - a file handle under the key `fp`
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
            shutil.copyfileobj(attachment.file , fs_attachment)
        fs_attachment.close()
        chmod(fs_attachment_path, 0660)
        self.paths_created.append(fs_attachment_path)
        return sanitized

    def process(self, purge_meta_data=True, testing=False):
        """ Calls the external helper scripts to (optionally) purge the meta data and then
            send the contents of the dropbox via email.
        """
        self.status = u'020 submitted'
        fs_process = join(self.container.settings['fs_bin_path'], 'process.sh')
        fs_config = join(self.container.settings['fs_bin_path'],
            'briefkasten%s.conf' % ('_test' if testing else ''))
        shellenv = environ.copy()
        shellenv['PATH'] = '%s:%s:/usr/local/bin/:/usr/local/sbin/' % (shellenv['PATH'], self.container.settings['fs_bin_path'])
        if self.num_attachments > 0:
            caller = call
        else:
            caller = call
        process_status = caller("%s -d %s -c %s" % (fs_process, self.fs_path, fs_config), shell=True,
            env=shellenv)
        if process_status != 0:
            import pdb; pdb.set_trace(  )
        return process_status

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

    @status.setter
    def status(self, state):
        with open(join(self.fs_path, u'status'), 'w') as status_file:
            status_file.write(state)
