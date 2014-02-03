from fabric import api as fab
from fabric.contrib.project import rsync_project

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

