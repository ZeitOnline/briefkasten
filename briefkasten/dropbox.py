# -*- coding: utf-8 -*-
from json import load, dumps
from os import mkdir, chmod, environ
from os.path import exists, join, splitext
from random import SystemRandom
from shutil import rmtree
from subprocess import call


allchars = '23456qwertasdfgzxcvbQWERTASDFGZXCVB789yuiophjknmYUIPHJKLNM'


def generate_drop_id(length=8):
    rng = SystemRandom()
    drop_id = ""
    for i in range(length):
        drop_id += rng.choice(allchars)
    return drop_id


def sanitize_filename(filename):
    """preserve the file ending, but replace the name with a random token """
    token = generate_drop_id()
    name, extension = splitext(filename)
    if extension:
        return '%s.%s' % (token, extension)
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

    def add_dropbox(self, message=None, attachments=None):
        return Dropbox(self, message=message, attachments=attachments)

    def get_dropbox(self, drop_id):
        if drop_id in self:
            return Dropbox(self, drop_id=drop_id)
        else:
            raise KeyError

    def destroy(self):
        rmtree(self.fs_path)

    def __contains__(self, drop_id):
        return exists(join(self.fs_path, drop_id))


class Dropbox(object):

    def __init__(self, container, drop_id=None, message=None, attachments=None):
        """ if drop_id is None, this will create a dropbox on the file system, if not, it will populate itself
        from a given instance.
        """
        self.container = container
        self.paths_created = []
        if drop_id is None:
            self.drop_id = drop_id = generate_drop_id()
            # create a folder for the submission
            self.fs_path = fs_dropbox_path = join(container.fs_path, drop_id)
            mkdir(fs_dropbox_path)
            chmod(fs_dropbox_path, 0770)
            self.paths_created.append(fs_dropbox_path)

            # write the message into a file
            self._write_message(fs_dropbox_path, 'message', message)
            self.message = message

            # write the attachment into a file
            self.num_attachments = 0
            if attachments is not None:
                fs_attachment_container = join(fs_dropbox_path, 'attach')
                mkdir(fs_attachment_container)
                chmod(fs_attachment_container, 0770)
                self.paths_created.append(fs_attachment_container)
                for attachment in attachments:
                    if attachment is None:
                        continue
                    fs_attachment_path = join(fs_attachment_container, sanitize_filename(attachment['filename']))
                    fs_attachment = open(fs_attachment_path, 'w')
                    for line in attachment['fp'].readlines():
                        if isinstance(line, unicode):
                            line = line.encode('utf-8')
                        fs_attachment.write(line)
                    fs_attachment.close()
                    chmod(fs_attachment_path, 0660)
                    self.paths_created.append(fs_attachment_path)
                    self.num_attachments += 1

            # create an editor token
            self.editor_token = editor_token = generate_drop_id()
            self._write_message(fs_dropbox_path, 'editor_token', editor_token)

        else:
            self.drop_id = drop_id
            self.fs_path = join(container.fs_path, drop_id)
            self.editor_token = open(join(self.fs_path, 'editor_token')).readline()
        self.fs_replies_path = join(self.fs_path, 'replies')

    def update_message(self, newtext):
        """ overwrite the message text. this also updates the corresponding file. """
        self._write_message(self.fs_path, 'message', newtext)

    def process(self, purge_meta_data=True, testing=False):
        """ Calls the external helper scripts to (optionally) purge the meta data and then
            send the contents of the dropbox via email.
        """
        fs_process = join(self.container.settings['fs_bin_path'], 'process.sh')
        fs_config = join(self.container.settings['fs_bin_path'],
            'briefkasten%s.conf' % ('_test' if testing else ''))
        shellenv = environ.copy()
        shellenv['PATH'] = '%s:%s:/usr/local/bin/:/usr/local/sbin/' % (shellenv['PATH'], self.container.settings['fs_bin_path'])
        return call("%s -d %s -c %s" % (fs_process, self.fs_path, fs_config), shell=True,
            env=shellenv)

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
        fs_reply = open(fs_reply_path, 'w')
        fs_reply.write(message.encode('utf-8'))
        fs_reply.close()
        chmod(fs_reply_path, 0660)
        self.paths_created.append(fs_reply_path)

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
        """ returns either 'new', 'submitted', 'processed'
            if the status is new or submitted and the message is deleted, we assume it has been processed.
            (also: the scripts could simply leave a file named 'status' and fill it with information.)
        """
        return "submitted"
