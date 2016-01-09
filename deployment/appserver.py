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
    fab.run("supervisorctl %s briefkasten" % action)


@task
def upload_theme():
    """ upload and/or update the theme with the current git state"""
    get_vars()
    with fab.settings(fab.hide('running')):
        local_theme_path = path.abspath(path.join(fab.env['config_base'], fab.env.instance.config['local_theme_path']))
        rsync('-av', '--delete', local_theme_path, '{host_string}:%s/' % AV['themes_dir'])


@task
def upload_pgp_keys():
    """ upload and/or update the PGP keys for editors, import them into PGP"""
    # TODO: use env vars instead:
    get_vars()
    upload_target = '/tmp/pgp_pubkeys.tmp'
    with fab.settings(fab.hide('running')):
        fab.run('rm -rf %s' % upload_target)
        fab.run('mkdir %s' % upload_target)
        local_key_path = path.join(fab.env['config_base'], fab.env.instance.config['local_pgpkey_path'])
        remote_key_path = '{apphome}/var/pgp_pubkeys/'.format(**AV)
        rsync('-av', local_key_path, '{host_string}:%s' % upload_target)
        fab.run('chown -R %s %s' % (AV['appuser'], remote_key_path))
        fab.run('chmod 700 %s' % remote_key_path)
        with fab.shell_env(GNUPGHOME=remote_key_path):
            fab.sudo('''gpg --import %s/*.pgp''' % upload_target,
                user=AV['appuser'], shell_escape=False)
        fab.run('rm -rf %s' % upload_target)
