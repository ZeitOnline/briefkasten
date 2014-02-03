# coding: utf-8
from fabric import api as fab
from fabric.contrib.project import rsync_project
from mr.awsome.ezjail.fabric import bootstrap
from fabric_scripts import _local_path, _rsync_project

fab.env.shell = '/bin/sh -c'


# shutup pyflakes
(bootstrap, )

def download_distfiles():
    _rsync_project(remote_dir='/usr/local/poudriere/distfiles',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)


def download_packages():
    _rsync_project(remote_dir='/usr/jails/basejail/poudriere_data/packages',
        local_dir=_local_path('downloads/'),
        delete=False, upload=False)



def upload_distfiles():
    pass
