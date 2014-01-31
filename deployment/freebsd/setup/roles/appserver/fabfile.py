from os import path
from fabric import api as fab
from fabric.contrib.project import rsync_project as rsync_project


fab.env.shell = "/usr/local/bin/bash -c"

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
            _rsync_project(remote_dir='%s/briefkasten' % _default_vars()['apphome'],
                local_dir="%s/deployment/freebsd/workdir/application/briefkasten" % _git_base(),
                delete=True)

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


def upload_project():
    """ upload the entire project, including theme, application, pgg keys etc. with the current git state"""
    _checkout_git()
    _upload_application()
    _upload_theme()


# - name: upload editor's public keys
#   connection: local
#   command: 'rsync -av --delete  -e "ssh -F ssh_config" {{ local_pgpkey_path }}/ appserver:{{apphome}}/var/pgp_pubkeys/'

# - name: set ownership
#   command: "chown -R {{appuser}} {{apphome}}"

# - name: import pgp keys
#   sudo_user: "{{appuser}}"
#   script: import-gpg.sh

# - name: run buildout (this *will* take quite a while... be patient)
#   command: gmake deployment chdir={{apphome}}
#   sudo_user: "{{appuser}}"
#   notify: restart supervisord
