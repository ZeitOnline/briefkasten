# coding: utf-8
from fabric import api as fab
from bsdploy.fabutils import rsync

fab.env.shell = '/bin/sh -c'


def download_distfiles():
    _rsync_project(remote_dir='/usr/local/poudriere/distfiles',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def upload_distfiles():
    _rsync_project(remote_dir='/usr/local/poudriere/distfiles/',
        local_dir=_local_path('downloads/distfiles/'),
        delete=True, upload=True)


def download_packages():
    _rsync_project(remote_dir='/usr/jails/basejail/poudriere_data/packages',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def upload_packages():
    _rsync_project(remote_dir='/usr/jails/basejail/poudriere_data/packages/',
        local_dir=_local_path('downloads/packages/'),
        delete=False, upload=True)


def download_ports_tree():
	""" download poudriere's ports tree """
	_rsync_project(remote_dir='/usr/local/poudriere/ports/default',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def upload_ports_tree():
	""" download poudriere's ports tree """
	_rsync_project(remote_dir='/usr/local/poudriere/ports/default/',
        local_dir=_local_path('downloads/default/'),
        delete=False, upload=True)


def download_poudriere_assets():
    """ download ports tree, distfiles, and packages from poudriere """
    download_distfiles()
    download_packages()
    download_ports_tree()


def upload_poudriere_assets():
    """ upload local ports tree, distfiles, and packages from poudriere """
    upload_distfiles()
    upload_packages()
    upload_ports_tree()


@fab.task
def download_options():
    rsync('-av', '{host_string}:/usr/local/etc/poudriere.d/102amd64-briefkasten-options', 'roles/poudriere/files/')


@fab.task
def build_packages():
    fab.run('poudriere bulk -f /usr/local/etc/poudriere.d/briefkasten-pkglist -p briefkasten -z briefkasten -j 102amd64')
