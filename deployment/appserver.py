# coding: utf-8
from os import path
from fabric import api as fab
from fabric.api import env, task
from bsdploy.fabutils import rsync
from ploy.config import value_asbool

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
    get_vars()
    upload_target = '/tmp/pgp_pubkeys.tmp'
    with fab.settings(fab.hide('running')):
        fab.run('rm -rf %s' % upload_target)
        fab.run('mkdir %s' % upload_target)
        local_key_path = path.join(fab.env['config_base'], fab.env.instance.config['local_pgpkey_path'])
        remote_key_path = '/var/briefkasten/pgp_pubkeys/'.format(**AV)
        rsync('-av', local_key_path, '{host_string}:%s' % upload_target)
        fab.run('chown -R %s %s' % (AV['appuser'], remote_key_path))
        fab.run('chmod 700 %s' % remote_key_path)
        with fab.shell_env(GNUPGHOME=remote_key_path):
            fab.sudo('''gpg --import %s/*.pgp''' % upload_target,
                user=AV['appuser'], shell_escape=False)
        fab.run('rm -rf %s' % upload_target)


@task
def upload_backend(index='dev', user=None):
    """
    Build the backend and upload it to the remote server at the given index
    """
    get_vars()
    login_devpi(user=user, index=index)
    with fab.lcd('../application'):
        fab.local('make upload')


def briefkasten_ctl(action='restart'):
    get_vars()
    fab.sudo('supervisorctl {action} briefkasten'.format(
        action=action,
        **AV), warn_only=True)


@task
def update_backend(index='dev', build=True, user=None, version=None):
    """
    Install the backend from the given devpi index at the given version on the target host and restart the service.

    If version is None, it defaults to the latest version

    Optionally, build and upload the application first from local sources. This requires a
    full backend development environment on the machine running this command (pyramid etc.)
    """
    get_vars()
    if value_asbool(build):
        upload_backend(index=index, user=user)
    with fab.cd('{apphome}'.format(**AV)):
        command = 'bin/pip install --upgrade --pre -i {ploy_default_publish_devpi}/briefkasten/{index}/+simple/ briefkasten'.format(
            index=index,
            user=user,
            **AV)
        if version:
            command = '%s==%s' % (command, version)
        fab.sudo(command)

    briefkasten_ctl('restart')


@task
def login_devpi(index='dev', user=None):
    get_vars()
    if user is None:
        user = fab.env['user']
    publish_devpi = AV.get('ploy_default_publish_devpi')
    login = fab.local(
        'bin/devpi use {base_url}/briefkasten/{index}'.format(
            index=index,
            base_url=publish_devpi,
        ),
        capture=True
    )
    if not login.splitlines()[0].endswith('(logged in as {user})'.format(user=user)):
        fab.local('bin/devpi login {user}'.format(user=user))
