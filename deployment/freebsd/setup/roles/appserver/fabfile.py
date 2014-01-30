from fabric import api as fab
from fabric.contrib.project import rsync_project


fab.env.shell = "/usr/local/bin/bash -c"


def debug():
    fab.run('pwd')


def upload_application():
    git_base = fab.local('git rev-parse --show-toplevel', capture=True)
    with fab.cd(git_base):
        # clean the workdir
        fab.local('rm -rf deployment/freebsd/workdir/*')
        # check out clean copy of the local git repo
        fab.local('git checkout-index -a -f --prefix=%s/deployment/freebsd/workdir/' % git_base)
        # upload application
        # We have to force a ssh connection, so the known hosts file is filled
        # with current data, otherwise the rsync_project call will fail
        fab.run('pwd')
        import pdb; pdb.set_trace()
        with fab.settings(fab.hide('running')):
            rsync_project('/mnt/data/content/',
                local_dir="deployment/freebsd/workdir/",
                delete=True,
                ssh_opts='-o UserKnownHostsFile=%s' % fab.env.known_hosts)


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
