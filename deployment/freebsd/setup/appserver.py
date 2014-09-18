from os import path
from fabric import api as fab
# from fabric_scripts import _git_base, _checkout_git
from bsdploy.fabutils import rsync_project


fab.env.shell = "/bin/csh -c"
# default_vars = _default_vars('appserver.yml')


def _upload_application():
    git_base = _git_base()
    
    with fab.lcd(git_base):
        with fab.settings(fab.hide('running')):
            # upload the whole project w/o deleting
            rsync_project(remote_dir=default_vars['apphome'],
                local_dir="%s/deployment/freebsd/workdir/application/" % git_base,
                delete=False)

            # upload the source with deleting
            rsync_project(remote_dir='%s/briefkasten' % default_vars['apphome'],
                local_dir="%s/deployment/freebsd/workdir/application/briefkasten/" % _git_base(),
                delete=True)
        fab.run('chown -R %s %s' % (default_vars['appuser'], default_vars['apphome']))


def upload_application():
    """upload and/or update the application with the current git state """
    _checkout_git()
    _upload_application()


def _upload_theme():
    with fab.lcd(_git_base()):
        with fab.settings(fab.hide('running')):
            local_theme_path = path.join(fab.env['config_base'], fab.env.instance.config['local_theme_path'])
            remote_theme_path = '%s/themes/%s' % (default_vars['apphome'], fab.env.instance.config['theme_name'])
            rsync_project(remote_dir=remote_theme_path,
                local_dir=local_theme_path,
                delete=True)


def upload_theme():
    """ upload and/or update the theme with the current git state"""
    _checkout_git()
    _upload_theme()


def upload_editor_keys():
    """ upload and/or update the PGP keys for editors, import them into PGP"""
    appuser = 'pyramid'
    apphome = '/usr/local/briefkasten'
    with fab.settings(fab.hide('running')):
        local_key_path = path.join(fab.env['config_base'], fab.env.instance.config['local_pgpkey_path'])
        remote_key_path = '%s/var/pgp_pubkeys/' % apphome
        rsync_project(remote_dir=remote_key_path, local_dir=local_key_path, delete=True)
        fab.run('chown -R %s %s' % (appuser, remote_key_path))
        with fab.prefix("setenv GNUPGHOME %s" % remote_key_path):
            fab.sudo('''gpg --import %s/*.gpg''' % remote_key_path,
                user=appuser, shell_escape=False)


def restart_application():
    fab.sudo('supervisorctl restart briefkasten')


def run_buildout():
    with fab.cd(default_vars['apphome']):
        fab.sudo('gmake deployment', user=default_vars['appuser'])
    restart_application()


def upload_project():
    """ upload, bootstrap and start the entire project"""
    _checkout_git()
    _upload_application()
    _upload_theme()
    upload_editor_keys()
    run_buildout()
