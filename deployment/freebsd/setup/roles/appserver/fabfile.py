from os import path
from fabric import api as fab
from fabric.contrib.project import rsync_project as rsync_project


fab.env.shell = "/bin/csh -c"

def _git_base():
    return fab.local('git rev-parse --show-toplevel', capture=True)


def _default_vars():
    import ansible
    pb = fab.env.server.get_playbook('../../appserver.yml')
    play = ansible.playbook.Play(pb, pb.playbook[0], pb.play_basedirs[0])
    return play.default_vars


def _rsync_project(*args, **kwargs):
    additional_args = []
    ssh_info = fab.env.server.init_ssh_key()
    for key in ssh_info:
        if key[0].isupper():
            additional_args.append('-o')
            additional_args.append('%s="%s"' % (key, ssh_info[key].replace('"', '\"')))
    kwargs['ssh_opts'] = '%s %s' % (kwargs.get('ssh_opts', ''), ' '.join(additional_args))
    rsync_project(*args, **kwargs)


def _checkout_git():
    with fab.lcd(_git_base()):
        # clean the workdir
        fab.local('rm -rf workdir/*')
        # check out clean copy of the local git repo
        fab.local('git checkout-index -a -f --prefix=%s/deployment/freebsd/workdir/' % _git_base())

def _upload_application():
    git_base = _git_base()
    default_vars = _default_vars()
    with fab.lcd(git_base):
        with fab.settings(fab.hide('running')):
            # upload the whole project w/o deleting
            _rsync_project(remote_dir=default_vars['apphome'],
                local_dir="%s/deployment/freebsd/workdir/application/" % git_base,
                delete=False)

            # upload the source with deleting
            _rsync_project(remote_dir='%s/briefkasten' % default_vars['apphome'],
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
            local_theme_path = path.join(fab.env['config_base'], fab.env.server.config['local_theme_path'])
            remote_theme_path = '%s/themes/%s' % (_default_vars()['apphome'], fab.env.server.config['theme_name'])
            _rsync_project(remote_dir=remote_theme_path,
                local_dir=local_theme_path,
                delete=True)


def upload_theme():
    """ upload and/or update the theme with the current git state"""
    _checkout_git()
    _upload_theme()


def upload_editor_keys():
    """ upload and/or update the PGP keys for editors, import them into PGP"""
    default_vars = _default_vars()
    appuser = default_vars['appuser']
    with fab.settings(fab.hide('running')):
        local_key_path = path.join(fab.env['config_base'], fab.env.server.config['local_pgpkey_path'])
        remote_key_path = '%s/var/pgp_pubkeys/' % _default_vars()['apphome']
        _rsync_project(remote_dir=remote_key_path, local_dir=local_key_path, delete=True)
        fab.run('chown -R %s %s' % (appuser, remote_key_path))
        with fab.prefix("setenv GNUPGHOME %s" % remote_key_path):
            fab.sudo('''gpg --import %s/*.gpg''' % remote_key_path,
                user=appuser, shell_escape=False)


def run_buildout():
    default_vars = _default_vars()
    with fab.cd(default_vars['apphome']):
        fab.sudo('gmake deployment', user=default_vars['appuser'])
#   notify: restart supervisord


def upload_project():
    """ upload, bootstrap and start the entire project"""
    _checkout_git()
    _upload_application()
    _upload_theme()
    upload_editor_keys()
    run_buildout()

