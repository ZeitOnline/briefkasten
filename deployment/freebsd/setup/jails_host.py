# coding: utf-8
from fabric import api as fab
from mr.awsome.ezjail.fabric import bootstrap as _bootstrap
from fabric_scripts import _local_path, _rsync_project, _default_vars

fab.env.shell = '/bin/sh -c'
default_vars = _default_vars('poudriere.yml')


def bootstrap(**kwargs):
    """call mr.awsome.ezjail's bootstrap """
    with fab.lcd(_local_path('provisioning/vm-master')):
        _bootstrap(**kwargs)


# poudriere tasks:

def download_distfiles():
    _rsync_project(remote_dir='/usr/local/poudriere/distfiles',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def download_packages():
    _rsync_project(remote_dir='/usr/jails/basejail/poudriere_data/packages',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def download_ports_tree():
	""" download poudriere's ports tree """
	_rsync_project(remote_dir='/usr/local/poudriere/ports/default',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def upload_distfiles():
    pass


def build_packages():
    """ uploads the list of packages and tells poudriere to build them"""
    pkg_list = default_vars['pkg_list']
    fab.put(_local_path('setup/roles/poudriere/files/pkg_list'), pkg_list)
    fab.run('poudriere bulk -f %s -j 92amd64' % pkg_list)
