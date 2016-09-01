# coding: utf-8
from fabric import api as fab
from fabric.api import env, task
from bsdploy.fabfile_mfsbsd import bootstrap as mfsbootstrap
from ploy.common import yesno
from ploy.config import value_asbool

AV = None

# hide stdout by default
# from fabric.state import output
# output['stdout'] = False


@task
def bootstrap(**kw):
    mfsbootstrap(**kw)


def get_vars():
    global AV
    if AV is None:
        hostname = env.host_string.split('@')[-1]
        AV = dict(hostname=hostname, **env.instances[hostname].get_ansible_variables())
    return AV


@task
def reset_cleansers(confirm=True):
    """destroys all cleanser slaves and their rollback snapshots, as well as the initial master
    snapshot - this allows re-running the jailhost deployment to recreate fresh cleansers."""

    if value_asbool(confirm) and not yesno("""\nObacht!
            This will destroy any existing and or currently running cleanser jails.
            Are you sure that you want to continue?"""):
        exit("Glad I asked...")

    get_vars()

    cleanser_count = AV['ploy_cleanser_count']
    # make sure no workers interfere:
    fab.run('ezjail-admin stop worker')
    # stop and nuke the cleanser slaves
    for cleanser_index in range(cleanser_count):
        cindex = '{:02d}'.format(cleanser_index + 1)
        fab.run('ezjail-admin stop cleanser_{cindex}'.format(cindex=cindex))
        with fab.warn_only():
            fab.run('zfs destroy tank/jails/cleanser_{cindex}@jdispatch_rollback'.format(cindex=cindex))
            fab.run('ezjail-admin delete -fw cleanser_{cindex}'.format(cindex=cindex))
            fab.run('umount -f /usr/jails/cleanser_{cindex}'.format(cindex=cindex))
            fab.run('rm -rf /usr/jails/cleanser_{cindex}'.format(cindex=cindex))

    with fab.warn_only():
        # remove master snapshot
        fab.run('zfs destroy -R tank/jails/cleanser@clonesource')

        # restart worker and cleanser to prepare for subsequent ansible configuration runs
        fab.run('ezjail-admin start worker')
        fab.run('ezjail-admin stop cleanser')
        fab.run('ezjail-admin start cleanser')


@task
def reset_jails(confirm=True, keep_cleanser_master=True):
    """ stops, deletes and re-creates all jails.
    since the cleanser master is rather large, that one is omitted by default.
    """
    if value_asbool(confirm) and not yesno("""\nObacht!
            This will destroy all existing and or currently running jails on the host.
            Are you sure that you want to continue?"""):
        exit("Glad I asked...")

    reset_cleansers(confirm=False)

    jails = ['appserver', 'webserver', 'worker']
    if not value_asbool(keep_cleanser_master):
        jails.append('cleanser')

    with fab.warn_only():
        for jail in jails:
            fab.run('ezjail-admin delete -fw {jail}'.format(jail=jail))
        # remove authorized keys for no longer existing key (they are regenerated for each new worker)
        fab.run('rm /usr/jails/cleanser/usr/home/cleanser/.ssh/authorized_keys')
