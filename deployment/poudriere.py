# coding: utf-8
from fabric import api as fab
from bsdploy.fabutils import rsync

fab.env.shell = '/bin/sh -c'


@fab.task
def download_distfiles():
    rsync('-av', '{host_string}:/usr/local/poudriere/distfiles', 'downloads/')


@fab.task
def upload_distfiles():
    rsync('-av', 'downloads/distfiles/', '{host_string}:/usr/local/poudriere/distfiles/')


@fab.task
def download_packages():
    rsync('-av', '{host_string}:/usr/jails/basejail/poudriere_data/packages',
        'downloads/')


@fab.task
def upload_packages():
    rsync('-av', '{host_string}:/usr/jails/basejail/poudriere_data/packages/',
        'downloads/packages/')


@fab.task
def download_options():
    rsync('-av', '{host_string}:/usr/local/etc/poudriere.d/111amd64-briefkasten-options', 'roles/poudriere/files/')


@fab.task
def build_packages():
    fab.run('poudriere bulk -f /usr/local/etc/poudriere.d/briefkasten-pkglist -p briefkasten -z briefkasten -j 111amd64')


@fab.task
def download_poudriere_assets():
    """ download ports tree, distfiles, and packages from poudriere """
    download_distfiles()
    download_packages()


@fab.task
def upload_poudriere_assets():
    """ upload local ports tree, distfiles, and packages from poudriere """
    upload_distfiles()
    upload_packages()


