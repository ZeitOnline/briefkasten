from fabric import api as fab
from fabric.contrib.project import rsync_project as _rsync_project


fab.env.shell = "/usr/local/bin/bash -c"


def debug():
    fab.run('ls')

def get_play(path):
    import ansible
    pb = fab.env.server.get_playbook(path)
    return ansible.playbook.Play(pb, pb.playbook[0], pb.play_basedirs[0])

def rsync_project(*args, **kwargs):
    additional_args = []
    ssh_info = fab.env.server.init_ssh_key()
    for key in ssh_info:
        if key[0].isupper():
            additional_args.append('-o')
            additional_args.append('%s="%s"' % (key, ssh_info[key].replace('"', '\"')))
    kwargs['ssh_opts'] = '%s %s' % (kwargs.get('ssh_opts', ''), ' '.join(additional_args))
    _rsync_project(*args, **kwargs)


def upload_application():
    git_base = fab.local('git rev-parse --show-toplevel', capture=True)
    play = get_play('../../appserver.yml')
    default_vars = play.default_vars
    with fab.lcd(git_base):
        # clean the workdir
        fab.local('rm -rf workdir/*')
        # check out clean copy of the local git repo
        fab.local('git checkout-index -a -f --prefix=%s/deployment/freebsd/workdir/' % git_base)
        # upload application
        with fab.settings(fab.hide('running')):
            rsync_project(remote_dir=default_vars['apphome'],
                local_dir="%s/deployment/freebsd/workdir/application/" % git_base,
                delete=False)


# - name: upload application
#   connection: local
#   command: 'rsync -av  -e "ssh -F ssh_config" workdir/application/ appserver:{{apphome}}/'

# - name: upload theme
#   connection: local
#   command: 'rsync -av  -e "ssh -F ssh_config" {{ local_theme_path }}/ appserver:{{apphome}}/themes/{{ theme_name }}'

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
