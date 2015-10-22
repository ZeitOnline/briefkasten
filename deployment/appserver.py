# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import env, task
from bsdploy.fabutils import rsync

AV = None

# hide stdout by default
# from fabric.state import output
# output['stdout'] = False


def get_vars():
    global AV
    if AV is None:
        hostname = env.host_string.split('@')[-1]
        AV = dict(hostname=hostname,
            **env.instances[hostname].get_ansible_variables())
    return AV


@task
def application(action="restart"):
    get_vars()
    fab.run("supervisorctl %s" % action)


@task
def upload_theme():
    """ upload and/or update the theme with the current git state"""
    get_vars()
    with fab.settings(fab.hide('running')):
        local_theme_path = path.abspath(path.join(fab.env['config_base'], fab.env.instance.config['local_theme_path']))
        rsync('-av', '--delete', local_theme_path, '{host_string}:%s/' % AV['themes_dir'])


def upload_editor_keys():
    """ upload and/or update the PGP keys for editors, import them into PGP"""
    appuser = 'pyramid'
    apphome = '/usr/local/briefkasten'
    with fab.settings(fab.hide('running')):
        local_key_path = path.join(fab.env['config_base'], fab.env.instance.config['local_pgpkey_path'])
        remote_key_path = '%s/var/pgp_pubkeys/' % apphome
        rsync(remote_dir=remote_key_path, local_dir=local_key_path, delete=True)
        fab.run('chown -R %s %s' % (appuser, remote_key_path))
        with fab.prefix("setenv GNUPGHOME %s" % remote_key_path):
            fab.sudo('''gpg --import %s/*.gpg''' % remote_key_path,
                user=appuser, shell_escape=False)


